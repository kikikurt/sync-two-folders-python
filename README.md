## sync-two-folders-python
This Python-based CLI tool synchronizes two folders using an asynchronous approach. 
It optimizes performance by validating synchronization based on file size and last modified date.

## Usage
```
python main.py [-s/--source SOURCE] [-r/--replica REPLICA] [-i/--interval INTERVAL] [-l/--logfile LOG_FILE]
```

- `-s/--source`: Path to source folder
- `-r/--replica`: Path to replica folder
- `-i/--interval`: Sync interval in secs
- `-l/--logfile`: Path to log file 

## Example
```
python main.py -s source_path -r replica_path -i 10 -l 'sync.log'
```


