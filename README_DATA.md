# CUL Data dumps

Current dumps from 2015-05 are about 150MB:

```
> ls -sh1 /cul/data/voyager/
total 148M
 43M charge-and-browse-counts.txt.gz
105M circ_trans.txt.gz

> zcat /cul/data/voyager/charge-and-browse-counts.txt.gz  | wc -l
8735672
> zcat /cul/data/voyager/circ_trans.txt.gz  | wc -l
10479934
```

These dumps are not publicly available. For testing there are some randomized data dumps of 1/100th the size in the [testdata](testdata) directory. These follow the same formatting as the real dumps.
