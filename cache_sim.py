"""
Implementation of a Cache simulation
"""
from collections import OrderedDict
import logging
import argparse
import sys
import datetime
import coloredlogs

class Cache:
    """
    Implements a caches
    """
    def __init__(self, max_cache_size=1, strategy='LRU', ttl_seconds=60):
        if max_cache_size < 0:
            raise AttributeError("max_cache_size < 0")
        if ttl_seconds < 0:
            raise AttributeError("ttl_seconds < 0")
        if strategy not in 'LRU':
            raise AttributeError("strategy not in ('LRU')")

        self.max_cache_size = max_cache_size
        self.strategy = strategy
        self.ttl_seconds = ttl_seconds
        logging.info(f'Initialising cache')
        logging.info(f' - Max size [req]: %s', self.max_cache_size)
        logging.info(f' - Strategy      : %s', self.strategy)
        logging.info(f' - TTL [Sec]     : %s', self.ttl_seconds)

        self.cache = {}
        self.cache_created = OrderedDict()
        self.cache_last_use = {}

        self.count_hits = 0
        self.count_misses = 0
        self.count_requests = 0
        self.start_time = None

    def count_elements(self):
        """
        Returns the current number of elements in the cache
        """
        return len(self.cache)

    def remove_item(self, key):
        """
        Removes the item from the cache
        """
        del self.cache[key]
        del self.cache_last_use[key]
        del self.cache_created[key]

    def displace_element(self):
        """
        Displaces one element from the cache based on the
        selected strategy.
        LRU = Least recently used
        """
        logging.debug(f'- Cache displacement: %s', self.strategy)
        if self.strategy == 'LRU':
            # find least recently used key
            min_date = None
            min_key = None
            for key, item_date in self.cache_last_use.items():
                if not min_date or item_date < min_date:
                    min_date = item_date
                    min_key = key

            logging.debug(f'  Removing Key %s from %s', min_key, min_date)
            if min_key in self.cache:
                self.remove_item(min_key)

    def run_request(self, request):
        """
        Runs a request through the cache
        """
        logging.debug(f'==================================================')
        logging.debug(f'Incoming request %s, TS %s', request["query"], request["timestamp"])

        self.count_requests += 1
        query = request['query']
        timestamp = request['timestamp']
        if not self.start_time:
            self.start_time = timestamp

        # Cache expiration strategy
        self.expire_cache(timestamp)

        # Cache hit ot miss?
        if query in self.cache:
            # Cache hit
            logging.debug('=> Cache hit')
            self.count_hits += 1
            self.cache[query] += 1
        else:
            # Cache miss
            self.count_misses += 1
            if self.count_elements() >= self.max_cache_size:
                # remove item based on strategy
                self.displace_element()

            self.cache[query] = 1
            self.cache_created[query] = timestamp
            logging.debug('=> Cache miss')

        self.cache_last_use[query] = timestamp

        # print some statistics
        logging.debug(f'Current cache size: %s [req]', self.count_elements())
        logging.debug(f'Total hits        : %s [req]', self.count_hits)
        logging.debug(f'Total misses      : %s [req]', self.count_misses)

    def expire_cache(self, current_time):
        """
        Expires items in the cache based on the TTL configurations
        """
        # update cache based on TTL expirations

        remove_keys = []
        # here, we are iterating through an OrderedDict. As items are
        # created in ascending order by created timestamp, we can break
        # loop as soon as an element is not expired
        for query_key, timestamp in self.cache_created.items():
            if current_time > timestamp + datetime.timedelta(seconds=self.ttl_seconds):
                remove_keys.append((query_key, timestamp))
            else:
                break

        if not remove_keys:
            logging.debug(f'- TTL expirations: -')
        else:
            logging.debug(f'- TTL expirations: %s requests', len(remove_keys))

        for (query_key, timestamp) in remove_keys:
            logging.debug(f'  Expiring request "%s" from %s', query_key, timestamp)
            self.remove_item(query_key)

    def run_requests_from_file(self, filename, max_req=None):
        """
        Runs a max_req number of requests from a file through the caching
        simulation
        """
        if max_req:
            logging.info('Replaying %s requests from file %s', max_req, filename)
        else:
            logging.info('Replaying all requests from file %s', filename)
        # f is an iterator to stream text file to avoid loading everything in memory
        i = 1
        num_lines = sum(1 for line in open(filename))

        with open(f'S_{self.max_cache_size}_T_{self.ttl_seconds}_{self.strategy}.csv', 'w') as out_file:
            # write header for statistics file
            out_file.write(f'Timestamp;cache size;hits count;miss count;requests;total requests\n')
            out_file.flush()
            with open(filename, 'r') as file:
                first = True
                for line in file:
                    if first:
                        first = False
                        continue
                    cols = line.split(';')
                    # e.g. 2021-04-01T00:00:01.038Z
                    timestamp = datetime.datetime.strptime(cols[1], "%Y-%m-%dT%H:%M:%S.%fZ")
                    req = {
                        'ID' : int(cols[0]),
                        'timestamp': timestamp,
                        'query': cols[2].strip()
                    }

                    self.run_request(req)
                    i += 1
                    if max_req and i > max_req:
                        return

                    if i % 10000 == 0:
                        logging.info(f'Processed {i / num_lines * 100:.2f}% requests ({i}/{num_lines})  Cache size {self.count_elements()} | Hits {self.count_hits} | {timestamp}')
                        out_file.write(f'{timestamp};{self.count_elements()};{self.count_hits};{self.count_misses};{i};{num_lines}\n')
                        out_file.flush()

if __name__ == '__main__':
    coloredlogs.install(level='DEBUG')

    # parse command line arguments
    PARSER = argparse.ArgumentParser(description='HTTP Response Cache Simulator',
                                     epilog="TODO: detailed description")
    PARSER.add_argument('-f', '--file', type=str, default='test_requests.csv', help='Input file')
    PARSER.add_argument('-s', '--size', type=float, default='10', help='Cache size in items')
    PARSER.add_argument('-t', '--ttl', type=int, default='60', help='Time to live in seconds')
    PARSER.add_argument('--batch', type=str, default='', help='Runs a batch, e.g. --batch True')

    ARGUMENTS = PARSER.parse_args(sys.argv[1:])

    if not ARGUMENTS.batch:
        # run simulation with one configuration
        CACHE = Cache(ARGUMENTS.size, 'LRU', ARGUMENTS.ttl)

        logging.info(f'Running simulation...')

        CACHE.run_requests_from_file(ARGUMENTS.file)

        logging.info(f'Finished')
        logging.info(f' - Cached requests: %s', CACHE.count_elements())
        logging.info(f' - Total requests : %s', CACHE.count_requests)
        logging.info(f' - Total hits     : %s', CACHE.count_hits)
        logging.info(f' - Total misses   : %s', CACHE.count_misses)
    else:
        # runs a batch simulation recording results for multiple configurations
        logging.info(f'Running batch simulation on {ARGUMENTS.file}...')

        with open(f'batch_result.csv', 'w') as out_file:
            out_file.write(f'Total requests;Cache Strategy;TTL [sec];TTL [min]; Cache Size;Hits;Misses;Efficiency [% cached];Data-file\n')
            out_file.flush()
            for size in (1000, 10000, 100000, 1000000):
                for ttl in (15, 30, 60, 2*60, 5*60, 10*60, 30*60, 60*60, 2*60*60, 4*60*60, 8*60*60):
                    CACHE = Cache(size, 'LRU', ttl)

                    logging.info(f'Running simulation...')

                    CACHE.run_requests_from_file(ARGUMENTS.file)

                    logging.info(f'Finished')
                    logging.info(f' - Cached requests: %s', CACHE.count_elements())
                    logging.info(f' - Total requests : %s', CACHE.count_requests)
                    logging.info(f' - Total hits     : %s', CACHE.count_hits)
                    logging.info(f' - Total misses   : %s', CACHE.count_misses)
                    out_file.write(f'{CACHE.count_requests};LRU;{ttl};{ttl/60};{size};{CACHE.count_hits};{CACHE.count_misses};{CACHE.count_hits/CACHE.count_requests};{ARGUMENTS.file}\n')
                    out_file.flush()

        logging.info(f'Finished')
