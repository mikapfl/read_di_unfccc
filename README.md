Dataset containing all data available from the UNFCCC API at https://di.unfccc.int. Also includes a small library to query the UNFCCC API for a subset of the data and a script to re-download all of the data.

Due to the large size of the full dataset, the dataset is shared using [datalad](https://www.datalad.org/), which is based on git. To download the data, see the dataset page on [gin](https://gin.g-node.org/mikapfl/read_di_unfccc) to download individual files from the data/ directory, or clone the whole dataset using datalad:
```shell
$ datalad clone https://github.com/mikapfl/read_di_unfccc.git
```
Then you can fetch the data using datalad:
```shell
$ cd read_di_unfccc
$ datalad get -r .
```
You can learn more about datalad in the [datalad handbook](http://handbook.datalad.org).

Sources of the data:
Most of the data is GHG inventory data that the UNFCCC provides as received from the parties, for details see the [UNFCCC GHG data website](https://unfccc.int/process/transparency-and-reporting/greenhouse-gas-data/what-is-greenhouse-gas-data).
While all of the data included in this dataset is available from the UNFCCC API, some of the data is included by the UNFCCC from other sources:
* For population data, the source is the UNSD Demographic Statistics accessible through [UNdata](http://data.un.org).
* For GDP data, the primary source is The World Bank, and the data is shared by The World Bank using the  CC-BY 4.0 License and pursuant to their [terms of use](https://data.worldbank.org/summary-terms-of-use).

If you want to use the library to download data from the UNFCCC API, check out the `example.ipynb` notebook for a simple usage example. To re-download all of the data, use the `download_all.py` script.

License: the python scripts are provided under the Apache License, Version 2.0.
