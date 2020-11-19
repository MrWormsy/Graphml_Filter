# Graphml_Filter
Small script used to filter a directory of graphml (or graphml.gz) files by given keys for the nodes and the edges.


### Usage
usage: python Graphml_Filter.py [SourcesPath] [ResultsPath] [NodesKeys] [EdgesKeys]

The arguments needed are the source path, the destination path and the nodes/edges keys to filter on

positional arguments:
  SourcesPath  The sources directory path (must exists)
  ResultsPath  The results directory path
  NodesKeys    The keys with the values the nodes must follow
  EdgesKeys    The keys with the values the edges must follow
  
### Example

  This command line will filter all the graphml files in the sources directory to keep only the Russian (RU) nodes and the other nodes connected to them (and no condition on the edges)
  ```{shell}
  python Graphml_Filter.py "./sources/" "./results/" "{'Country': ['RU']}" "{}"
  ```
