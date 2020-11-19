import argparse
import gzip
import logging
import os
import xml.etree.ElementTree as ET
from ast import literal_eval
from xml.etree.ElementTree import ElementTree


def getGraphmlFiles(dirPath):
    """Retrieve all the graphml files from the directory and parse them as XML trees

    Parameters
    ----------
    dirPath : str
        The path where the graphml files are

    Returns
    -------
    dict
        a dict with the name of the file as keys and the XML trees as values
    None
    """

    # Dict of the data from the graphml files
    treeDataDict = {}

    # Loop trough all the files in the directory
    for file in os.listdir(dirPath):

        # If the file ends with .graphml.gz that means it if a compressed graphml file,
        # we need to decompress it and then read it
        if file.endswith(".graphml.gz"):

            # Get the data of the compressed file
            fileData = gzip.open(dirPath + file, 'rb').read()

            # Append the data to the dict by its file name
            treeDataDict[file.replace('.graphml.gz', '')] = ET.fromstring(fileData)

        # Else if it a "classic" graphml file we simply read it
        elif file.endswith(".graphml"):

            # Add the data to the dict
            treeDataDict[file.replace('.graphml', '')] = ET.parse(dirPath + file).getroot()

    # Then we return this dict
    return treeDataDict


def filterTreeDataDictFromKeys(treeDataDict, resultdirectory, nodeKeys, edgesKeys):
    """Filter a tree from nodes/edges keys and save them back to a result directory

    Parameters
    ----------
    treeDataDict : dict
        dict containing the XML trees that need to be filtered

    resultdirectory : str
        path to results directory where the filtered trees will be saved

    nodeKeys : str
        dict containing the keys and the values that a node must have (can be empty)

    edgesKeys : str
        dict containing the keys and the values that a edge must have (can be empty)
    """

    # The namespace must be given...
    namespace = {"": "http://graphml.graphdrawing.org/xmlns"}

    # Used to save the file without the namespace
    ET.register_namespace('', 'http://graphml.graphdrawing.org/xmlns')

    # The keys mapped with the values used to fulfil conditions (to keep the nodes/edges that we want)
    nodesKeysToWatch = {}
    edgesKeysToWatch = {}
    keysAlreadyFound = False

    # We want to loop through every trees
    for keyTreeName in treeDataDict:

        # If this is not the first time we are looking for the keys we can continue
        # because the keys used are the same for all the trees of the function
        if not keysAlreadyFound:

            # We need to get the keys and know which key is mapped with the field we want to keep
            for key in treeDataDict[keyTreeName].findall('key', namespace):

                # We check which key is needed for the nodes and for the edges
                if key.attrib['for'] == "node" and key.attrib['attr.name'] in nodeKeys.keys():
                    # We want to map the key id to the values of the attribute name of the nodeKeys
                    nodesKeysToWatch[key.attrib['id']] = nodeKeys[key.attrib['attr.name']]

                if key.attrib['for'] == "edge" and key.attrib['attr.name'] in edgesKeys.keys():
                    # We want to map the key id to the values of the attribute name of the edgeKeys
                    edgesKeysToWatch[key.attrib['id']] = edgesKeys[key.attrib['attr.name']]

            # Tell that the keys have been found
            keysAlreadyFound = True

        # Get the graph
        graph = treeDataDict[keyTreeName].find("graph", namespace)

        # The nodes we want to keep
        nodesToKeep = set()

        # In the first place we want to gather all the nodes that fulfil given conditions
        for node in graph.findall("node", namespace):

            # We need to loop in every keys the node must have (if no condition is set we accept everything)
            if len(nodesKeysToWatch) > 0:

                # We loop through the keys needed
                for key in nodesKeysToWatch:

                    # If the node has a data key equal to what we are looking for
                    if node.find(".//data[@key='%s']" % key, namespace).text in nodesKeysToWatch[key]:
                        # Add the node to the ones we want to keep
                        nodesToKeep.add(node.attrib["id"])

            # No condition = accept every nodes
            else:

                # Add the node to the ones we want to keep
                nodesToKeep.add(node.attrib["id"])

        # Edges ids
        edgesToKeep = set()

        # set of "foreign" nodes that will be gathered in the loop below (the ones connected to the needed ones)
        newNodesToKeep = set()

        # Then we should have a set of nodes ids and we want to get the edges connected to those nodes
        for edge in graph.findall("edge", namespace):

            # If the source or the target is in the ids set we keep this edge
            if edge.attrib["source"] in nodesToKeep or edge.attrib["target"] in nodesToKeep:

                # We need to loop in every keys the node must have (if no condition is set we accept everything)
                if len(edgesKeysToWatch) > 0:

                    # We loop through the keys needed
                    for key in edgesKeysToWatch:

                        # If the edge has a data key equal to what we are looking for
                        if edge.find(".//data[@key='%s']" % key, namespace).text in edgesKeysToWatch[key]:
                            # Add the edge to the ones we want to keep
                            edgesToKeep.add(edge.attrib["id"])

                            # And add both the source and the target in the new nodes ids set as maybe one of them is
                            # not part of the initial nodesToKeep set and we must add them (to have the foreign nodes
                            # connected to the ones we want)
                            newNodesToKeep.add(edge.attrib["source"])
                            newNodesToKeep.add(edge.attrib["target"])

                # No condition = accept every edges
                else:
                    # Add the node to the ones we want to keep
                    edgesToKeep.add(edge.attrib["id"])

                    # And add both the source and the target in the new nodes ids set as maybe one of them is
                    # not part of the initial nodesToKeep set and we must add them (to have the foreign nodes
                    # connected to the ones we want)
                    newNodesToKeep.add(edge.attrib["source"])
                    newNodesToKeep.add(edge.attrib["target"])

        # We merge the two nodes sets
        nodesToKeep = nodesToKeep.union(newNodesToKeep)

        # Now that we have our nodes and edges we will loop the document and remove the ones we dont want
        for node in graph.findall('node', namespace):
            if not (node.attrib['id'] in nodesToKeep):
                graph.remove(node)

        for edge in graph.findall('edge', namespace):
            if not (edge.attrib['id'] in edgesToKeep):
                graph.remove(edge)

        # Finally save the new graph in the result directory (with the same name)
        ElementTree(treeDataDict[keyTreeName]).write(resultdirectory + keyTreeName + ".graphml")


if __name__ == '__main__':
    """
    Main function
    """

    # Create the parser
    parser = argparse.ArgumentParser(
        description='The arguments needed are the source path, the destination path and the nodes/edges keys to filter on')

    # Add the arguments
    parser.add_argument('sourcesPath', metavar='SourcesPath', nargs="?",
                        help='The sources directory path (must exists)', default="./sources/")
    parser.add_argument('resultsPath', metavar='ResultsPath', nargs="?", help='The results directory path',
                        default="./results/")
    parser.add_argument('nodesKeys', metavar='NodesKeys', nargs="?",
                        help='The keys with the values the nodes must follow', default='{"Country": ["RU"]}')
    parser.add_argument('edgesKeys', metavar='EdgesKeys', nargs="?",
                        help='The keys with the values the edges must follow', default="{}")

    # Parse the arguments
    args = parser.parse_args()

    # Get the path where to find the sources
    sourcesPath = vars(args)["sourcesPath"]

    # Check if the destination file exists (else raise an Exception)
    if not os.path.exists(sourcesPath):
        raise FileNotFoundError("%s path does not exist" % sourcesPath)

    # Get the path where to save the filtered files
    resultsPath = vars(args)["resultsPath"]

    # We try to parse the keys as a dict, if it fails we abort
    try:
        nodeKeys = literal_eval(vars(args)["nodesKeys"])
    except ValueError:
        raise

    try:
        edgesKeys = literal_eval(vars(args)["edgesKeys"])
    except ValueError:
        raise

    # Create the results directory if it does not exist yet
    if not os.path.exists(resultsPath):

        # Create the directory
        os.makedirs(resultsPath)
        logging.info("Results directory has been created")
    else:
        logging.info("Results directory already exists")

    # Gather the data from the graphml files in the source directory
    treeDataDict = getGraphmlFiles(sourcesPath)

    # Filter the trees and save them back into the results directory (filtered from given keys)
    # For example if we only want to keep the nodes from Russia (RU) and keep the nodes connected to them
    # The nodeKeys will be {"Country": ["RU"]}
    filterTreeDataDictFromKeys(treeDataDict, resultsPath, nodeKeys, edgesKeys)

    print("The files have been filtered")
