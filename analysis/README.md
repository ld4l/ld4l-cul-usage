# Analysis of Cornell usage data

## Analysis run to look at different metrics

Run on full usage data:

```
simeon@RottenApple ld4l-cul-usage>time ./parse_cul_usage_data.py -v --analyze --charge-and-browse=/cul/data/voyager/charge-and-browse-counts.txt.gz --circ-trans=/cul/data/voyager/circ_trans.txt.gz 
INFO:root:STARTED at 2015-06-25 14:09:20.157691
INFO:root:Reading charge and browse counts from /cul/data/voyager/charge-and-browse-counts.txt.gz
...warnings snipped...
INFO:root:Reading circulation transactions from /cul/data/voyager/circ_trans.txt.gz
INFO:root:Writing charge_dist.dat...
INFO:root:Writing browse_dist.dat...
INFO:root:Writing circ_dist.dat...
INFO:root:Writing usage_venn.dat...
INFO:root:FINISHED at 2015-06-25 14:13:42.725385

real		   4m22.759s
user		   4m20.916s
sys		   0m1.376s
```

Then the files `charge_dist.dat`, `browse_dist.dat`, and `circ_dist.dat` have the distributions of counts for historical charges, browses, and circulation transactions. The file `usage_venn.dat` has Venn diagram data for overlap of the metrics which is represents graphically in:

![Venn diagram of metric data overlaps](usage_venn.png)


```
simeon@RottenApple ld4l-cul-usage>time ./parse_cul_usage_data.py -v --charge-and-browse=/cul/data/voyager/charge-and-browse-counts.txt.gz --circ-trans=/cul/data/voyager/circ_trans.txt.gz 
INFO:root:STARTED at 2015-06-25 15:35:38.839019
INFO:root:Reading charge and browse counts from /cul/data/voyager/charge-and-browse-counts.txt.gz
...warnings snipped...
INFO:root:Reading circulation transactions from /cul/data/voyager/circ_trans.txt.gz
INFO:root:Writing raw_scores_dist.dat...
INFO:root:Writing stackscore_dist.dat...
INFO:root:FINISHED at 2015-06-25 15:39:36.657549

real	3m57.982s
user	3m56.761s
sys	0m0.983s
```