'''
Utility methods for manipulating clusters and cluster sequences
'''
from __future__ import print_function
from __future__ import division

from math import ceil
import bisect
import logging

logger = logging.getLogger(__name__)


class Cluster(object):

    def __init__(self, count, arrival, departure):
        if count<=0:
            print("count: "+str(count))
        assert count > 0, 'Cluster count must be greater than 0'
        assert (departure - arrival) > 0, 'Cluster duration must be greater than 0'
        self.count = count
        self.arrival = arrival
        self.departure = departure

    def __repr__(self):
        return '{}(count={}, arrival={}, departure={})'.format(self.__class__.__name__,
                                                               self.count,
                                                               self.arrival,
                                                               self.departure)

    def __hash__(self):
        return hash(tuple([self.count, self.arrival, self.departure]))

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and other.count == self.count
                and other.arrival == self.arrival
                and other.departure == self.departure)

    def __ne__(self, other):
        return not self == other

    @property
    def duration(self):
        return self.departure - self.arrival

    @property
    def flowrate(self):
        return self.count / self.duration

    def merge(self, cluster):
        if cluster is None:
            return self

        merged_count = self.count + cluster.count
        merged_arrival = min(self.arrival, cluster.arrival)
        merged_departure = max(self.departure, cluster.departure)

        return Cluster(count=merged_count,
                       arrival=merged_arrival,
                       departure=merged_departure)

    def merge_by_threshold(self, cluster, threshold):
        assert cluster is not None
        gap = max(self.arrival - cluster.departure,
                  cluster.arrival - self.departure)
        if gap <= threshold:
            return self.merge(cluster)

    def shift(self, offset):
        return Cluster(count=self.count,
                       arrival=(self.arrival + offset),
                       departure=(self.departure + offset))

    def split(self, time, min_cluster_size=-float('inf')):

        if time >= self.departure:
            head = self
            tail = None
            return head, tail

        if time <= self.arrival:
            head = None
            tail = self
            return head, tail

        head_ratio = (time - self.arrival) / self.duration
        head_count = self.count * head_ratio
        head_arrival = self.arrival
        head_departure = time
        if head_count >= min_cluster_size:
            head = Cluster(count=head_count,
                           arrival=head_arrival,
                           departure=head_departure)
        else:
            head = None

        tail_count = self.count * (1 - head_ratio)
        tail_arrival = time
        tail_departure = self.departure
        if tail_count >= min_cluster_size:
            tail = Cluster(count=tail_count,
                           arrival=tail_arrival,
                           departure=tail_departure)
        else:
            tail = None

        return head, tail

    def split_by_ratio(self, ratio, min_cluster_size=-float('inf')):
        assert ratio >= 0 and ratio <= 1, 'Split ratio should be between 0 and 1 (inclusive)'
        
        if ratio == 1:
            head = self
            tail = None
            return head, tail

        if ratio == 0:
            head = None
            tail = self
            return head, tail

        head_count = self.count * ratio
        head_arrival = self.arrival
        head_departure = self.arrival + self.duration * ratio
        if head_count >= min_cluster_size:
            head = Cluster(count=head_count,
                           arrival=head_arrival,
                           departure=head_departure)
        else:
            head = None

        tail_count = self.count * (1 - ratio)
        tail_arrival = head_departure
        tail_departure = self.departure
        if tail_count >= min_cluster_size:
            tail = Cluster(count=tail_count,
                           arrival=tail_arrival,
                           departure=tail_departure)
        else:
            tail = None

        return head, tail

    def expected_proportion(self, ratio, min_cluster_size=-float('inf')):
        assert ratio >= 0 and ratio <= 1, 'Split ratio should be between 0 (exclusive) and 1 (inclusive)'

        expected_count = self.count * ratio

        if expected_count >= min_cluster_size:
            expected_cluster = Cluster(count=expected_count,
                                       arrival=self.arrival,
                                       departure=self.departure)
        else:
            expected_cluster = None

        return expected_cluster

    def proportion(self, ratio, min_cluster_size=-float('inf')):
        head, tail = self.split_by_ratio(ratio, min_cluster_size)
        return head

    def copy(self):
        cluster = Cluster(count=self.count,
                          arrival=self.arrival,
                          departure=self.departure)
        return cluster

    def slice(self, start, end, min_cluster_size=-float('inf')):
        before_start, after_start = self.split(start, min_cluster_size)
        if after_start:
            before_end, after_end = after_start.split(end, min_cluster_size)
            return before_end


class ClusterSequence(object):

    # Properties of cluster sequences: Precedence
    
    def __init__(self, sequence=None):
        if sequence is None:
            self._clusters = []
        else:
            self._clusters = sorted(sequence, key=self._key)
        self._keys = [self._key(cluster) for cluster in self._clusters]

    def _key(self, cluster):
        return cluster.arrival

    def __len__(self):
        return len(self._keys)

    def __iter__(self):
        return iter(self._clusters)

    def __getitem__(self, index):
        return self._clusters[index]

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               self._clusters)

    def __bool__(self):
        return len(self) > 0

    def __hash__(self):
        return hash(tuple(self._clusters))

    def __eq__(self, other):
        class_check = isinstance(other, self.__class__)
        len_check = (len(self) == len(other))
        equality_check = class_check and len_check
        if equality_check:
            for index, cluster in enumerate(self):
                equality_check = (equality_check and
                                  cluster == other[index])
        return equality_check

    def __ne__(self, other):
        return not self == other

    def pop(self, index):
        self._keys.pop(index)
        return self._clusters.pop(index)

    def set(self, index, cluster):
        key = self._key(cluster)
        if self.setting_disrupts_order(index, key):
            raise InsertionError(cluster, index)
        self._keys[index] = key
        self._clusters[index] = cluster

    # Also check this for built-in setters
    def setting_disrupts_order(self, index, key):
        return ((index > 0 and key < self._keys[index-1])
                or
                (index < (len(self._keys) - 1) and key > self._keys[index+1]))

    def insort(self, cluster, merge=False):
        key = self._key(cluster)
        index = bisect.bisect_left(self._keys, key)
        self._insert(index, cluster, merge)
        return index

    def insert(self, index, cluster, merge=False):
        assert 0 <= index <= len(self._keys), 'index not in allowed range'
        try:
            self._check_insertion(index, cluster)
        except InsertionError as error:
            logger.debug(error.msg)
            raise
        else:
            self._insert(index, cluster, merge)

    def _insert(self, index, cluster, merge):
        key = self._key(cluster)
        if merge and key in self._keys:
            self._merge_and_replace(key, cluster)
        else:
            self._keys.insert(index, key)
            self._clusters.insert(index, cluster)

    def _merge_and_replace(self, key, cluster):
        index = self._keys.index(key)
        self._clusters[index] = self._clusters[index].merge(cluster)

    def _check_insertion(self, index, cluster):
        key = self._key(cluster)

        if index > 0 and key < self._keys[index-1]:
            raise InsertionError(cluster, index)
        if index < len(self._keys) and key > self._keys[index]:
            raise InsertionError(cluster, index)

    def append(self, cluster, merge=False):
        if cluster is None:
            return
        index = len(self._keys)
        self.insert(index, cluster, merge)

    def fuse(self):
        fused = None
        for cluster in self:
            fused = cluster.merge(fused)
        return fused

    # TODO: Rename merge param
    def merge(self, sequence, merge=True):

        #Odd
        if len(self) == 0 and sequence is not None:
            return sequence

        if sequence is None or len(sequence) == 0:
            return self

        merged = ClusterSequence()
        for cluster in self:
            merged.insort(cluster, merge=merge)
        for cluster in sequence:
            merged.insort(cluster, merge=merge)
        return merged

    def merge_by_threshold(self, threshold, Gmax=float('inf'), startup_lost_time=0):
        # Return merged indices, modifies cluster sequence in-place
        # Be consistent; either create copies or merge in-place
        merged_arrivals = {}

        head_index = 0
        tail_index = 1

        while tail_index < len(self):

            merged = self[head_index].merge_by_threshold(cluster=self[tail_index],
                                                         threshold=threshold)
            if merged and (merged.duration <= (Gmax - startup_lost_time)):
                try:
                    merged_arrivals[self[head_index].arrival].append(self[tail_index].arrival)
                except KeyError:
                    merged_arrivals[self[head_index].arrival] = [self[tail_index].arrival]
                self._clusters[head_index] = merged
                self._keys[head_index] = self._key(merged)
                self._clusters.pop(tail_index)
                self._keys.pop(tail_index)
                continue
            head_index += 1
            tail_index += 1
        return merged_arrivals

    @staticmethod
    def merge_all(sequence_list):
        merged = ClusterSequence()
        for sequence in sequence_list:
            merged = merged.merge(sequence)
        return merged

    def shift(self, offset):
        self._keys = [key+offset for key in self._keys]
        for cluster in self._clusters:
            cluster.arrival += offset
            cluster.departure += offset

    def slice(self, start, end, min_cluster_size=-float('inf')):
        result = ClusterSequence()

        if start >= self._clusters[-1].departure or end <= self._clusters[0].arrival:
            return result

        # TODO: Use bisect
        for index in range(len(self._keys)):
            if start < self._clusters[index].departure:
                start_index = index
                break

        for index in range(len(self._keys)-1, -1, -1):
            if end > self._clusters[index].arrival:
                end_index = index
                break

        if end_index >= start_index:
            for index in range(start_index, end_index + 1):
                sliced = self._clusters[index].slice(start, end, min_cluster_size)
                if sliced:
                    result.append(sliced)

        return result

    def unschedule(self, start, end, min_cluster_size=-float('inf')):
        removed_indices = []

        if start >= self._clusters[-1].departure or end <= self._clusters[0].arrival:
            return removed_indices

        for index in range(len(self._keys)):
            if start < self._clusters[index].departure:
                start_index = index
                break

        for index in range(len(self._keys)-1, -1, -1):
            if end > self._clusters[index].arrival:
                end_index = index
                break

        head, tail = self._clusters[start_index].split(start, min_cluster_size)
        if head is None:
            removed_indices.append(start_index)
        else:
            self._keys[start_index] = head.arrival
            self._clusters[start_index] = head

        head, tail = self._clusters[end_index].split(end, min_cluster_size)
        if tail is None:
            removed_indices.append(end_index)
        else:
            self._keys[end_index] = tail.arrival
            self._clusters[end_index] = tail

        if (end_index - start_index) > 1:
            for index in range(start_index+1, end_index):
                removed_indices.append(index)

        self._keys = [key for index, key in enumerate(self._keys)
                      if index not in removed_indices]
        self._clusters = [cluster for index, cluster in enumerate(self._clusters)
                          if index not in removed_indices]

        return removed_indices

    def copy(self):
        sequence = ClusterSequence()
        for cluster in self:
            sequence.append(cluster.copy())
        return sequence


class InsertionError(Exception):
    def __init__(self, cluster, index):
        super(InsertionError, self).__init__()
        self.msg = "Insertion of {} at index {} disturbs cluster order, operation not allowed".format(cluster, index)
