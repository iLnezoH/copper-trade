import networkx as nx
import matplotlib.pyplot as plt
import collections
import math

from networkx.algorithms.swap import connected_double_edge_swap

from src.modules.utils import getEntropy, getAdjacencyDegree, getStrength, getSelectionProbability, getAdjacencyEntropy

import time
import json


class Net():
    nx = nx

    def __init__(self, data) -> None:
        self.data = data
        self.initialEdges = []
        self._strengths = None
        self._adjacencyDegrees = None
        self._Es = None
        with open('src/data/database/country.json') as f:
            self.countries = json.load(f)

        self.G = self._generateNet(data)

    def _generateNet(self, data):

        G = nx.DiGraph()
        netData = data.netData

        for line in netData:
            exportNode = int(line[0])
            importNode = int(line[1])
            # G.add_node(line[0], label=data.getCountryName(line[0]))
            # G.add_node(line[1], label=data.getCountryName(line[1]))
            G.add_node(exportNode, label=self.countries[str(exportNode)])
            G.add_node(importNode, label=self.countries[str(importNode)])

            G.add_edge(exportNode, importNode,
                       weight=line[3])
        return G

    def freshGraph(self):
        self._strengths = None
        self._adjacencyDegrees = None
        self._Es = None

    def _repeatEdgeCheck(self, u, v):
        for (_u, _v) in self.initialEdges:
            if _u == u and _v == v:
                return True
        return False

    def getEntropy(self):

        degreeCount = self.getDegreeCount()

        distribute = list(degreeCount.values())
        amount = sum(distribute)

        E0 = getEntropy([x/amount for x in distribute])

        return E0

    def getStrength(self, node, l=0.75):
        return getStrength(self.G, node, l)

    def getAdjacencyDegree(self, node, theta=0.75, l=0.75):
        return getAdjacencyDegree(self.G, node, theta, l)

    def getSelectionProbability(self, i, j, theta=0.75, l=0.75):
        return getSelectionProbability(self.G, i, j, theta, l)

    def getAdjacencyEntropy(self, i, theta=0.75, l=0.75):
        return getAdjacencyEntropy(self.G, i, theta, l)

    def getStrengths(self, l=0.75):
        if (self._strengths is not None):
            return self._strengths
        strengths = {}
        for node in self.G.nodes:
            strengths[node] = self.getStrength(node, l)

        self._strengths = strengths

        return self._strengths

    def getAdjacencyDegrees(self, theta=0.75, l=0.75):
        if self._adjacencyDegrees is not None:
            return self._adjacencyDegrees

        _adjacencyDegrees = {}
        strengths = self.getStrengths(l)

        for node in self.G.nodes:
            successors = self.G.successors(node)
            predecessors = self.G.predecessors(node)

            in_strengths = sum([strengths[in_node]
                               for in_node in predecessors])
            out_strengths = sum([strengths[out_node]
                                for out_node in successors])

            _adjacencyDegrees[node] = theta * \
                in_strengths + (1 - theta) * out_strengths

        self._adjacencyDegrees = _adjacencyDegrees

        return _adjacencyDegrees

    def getAdjacencyEntropies(self, theta=0.75, l=0.75):
        if (self._Es is not None):
            return self._Es
        Es = {}

        strengths = self.getStrengths()
        adjacencyDegrees = self.getAdjacencyDegrees()

        for i in self.G.nodes:
            neighbors = self.getNeighbors(i)
            E = 0
            strength = strengths[i]
            for neighbor in neighbors:
                if strength == 0:
                    continue
                p = strength / adjacencyDegrees[neighbor]
                E += abs(p * math.log(p, 2))

            Es[i] = E

        return Es

    @property
    def sortedNodes(self):
        entropiesDict = self.getAdjacencyEntropies()
        entropiesArr = [
            {
                "name": self.data.getCountryName(code),
                "code": code,
                "E": E
            } for code, E in entropiesDict.items()
        ]

        return sorted(entropiesArr, key=lambda e: e["E"], reverse=True)

    def getNeighbors(self, node):
        successors = self.G.successors(node)
        predecessors = self.G.predecessors(node)

        return set((*successors, *predecessors))

    def drawEntropiesBar(self, count=20, width=0.8, color="b"):
        sortedEntropies = self.sortedNodes
        countries = []
        Es = []
        for item in sortedEntropies:
            countries.append(item["name"])
            Es.append(item["E"])

        plt.figure(figsize=(20, 5))
        plt.bar(countries[:count], Es[:count], width=width, color=color)
        plt.show()

    def getDegreeCount(self):
        degree_sequence = sorted(
            [d for n, d in self.G.degree()], reverse=True)  # degree sequence

        return collections.Counter(degree_sequence)

    def degreeDisBar(self, width=0.8, color="b"):
        G = self.G

        degreeCount = self.getDegreeCount()

        deg, cnt = zip(*degreeCount.items())

        plt.bar(deg, cnt, width=width, color=color)
        plt.show()

    def draw(self):
        G = self.G

        nodeStrength = list(G.degree(weight="tradeValue"))

        sortedNodeStrenght = sorted(nodeStrength, key=lambda item: item[1])

        minStrength = sortedNodeStrenght[0][1]
        maxStrength = sortedNodeStrenght[-1][1]

        node_sizes = [
            300 + (item[1] - minStrength)
            / (maxStrength - minStrength)
            * 6000
            for item in nodeStrength
        ]

        plt.figure(figsize=(30, 20))
        pos = nx.random_layout(G)
        # pos = nx.spiral_layout(G)
        nx.draw(G, pos, with_labels=False, node_size=node_sizes)

        node_labels = nx.get_node_attributes(G, 'label')
        nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=20)

        # edge_labels = nx.get_edge_attributes(G, 'tradeValue')
        # nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=20)

        plt.show()

    def removeTest(self, to_remove_series=None):
        G = nx.DiGraph.copy(self.G)
        connected_components_num_series = [
            len(list(nx.weakly_connected_components(G)))]
        for node in to_remove_series:
            G.remove_node(node)
            connected_components_num_series.append(
                len(list(nx.weakly_connected_components(G))))

        max_num = max(connected_components_num_series)

        # return [item / max_num for item in connected_components_num_series]
        return connected_components_num_series
