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

Then the files `charge_dist.dat`, `browse_dist.dat`, and `circ_dist.dat` have the distributions of counts for historical charges, browses, and circulation transactions. The file `usage_venn.dat` has Venn diagram data for overlap of the three metrics which is represented graphically in:

![Venn diagram of metric data overlaps](usage_venn.png)

There is data for a total of 2345788 `bib_ids`. The very small numbers of `bib_ids` represented in the circulation transactions which have no matching entry in the charge counts are likely records for items that have been deleted. Otherwise, this overlap provides confirmation that all circulation transactions have been reflected in the charge counts.

The gnuplot file `metric_distributions.gnu` plots the distributions of data from the three metrics on the same plot. The results demonstrate very similar forms for the metrics, and even very similar scales. PDF in `metric_distributions.pdf`: 

![Comparison of data distributions from the different metrics](metric_distributions.png)

## Computing a StackScore and comparing with Harvard data

Run code (done 2015-06-25, commit eed4518638b496d0c5f11d48f0e7c1a41c901c5b) without the `--analyze` option to compute raw score and normalized StackScore:

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

The code doesn't actually write out the `bib_id`->StackScore mappings at present, but writes information about the distributions. It also doesn't have access to all Cornell bibliographic records so it assumed a total of 7M records where any not included in the usage data have no usage data.

The StackScore is an interger from 1 to 100 where 1 is intended to indicates lowest community use, and 100 highest community use. The distribution of StackScore values in Harvard data (as used for [StackLife](http://stacklife.harvard.edu/) where higher scores are represented with a darker blue for the book spine and metadata summary block) is in `harvard_stackscore_distribution.dat`. Details of the sources of data used and the generation of these scores are given in [Paul Deschner's slides](https://wiki.duraspace.org/download/attachments/68060801/LD4L%20Usage%20Data.pdf?version=1&modificationDate=1425566384182&api=v2) from the [LD4L workshop](https://wiki.duraspace.org/display/ld4l/LD4L+Workshop+Agenda). Some features of the data are:

  1. There are ~13.5M items
  2. 98% of these items are assigned the lowest score of 1, this is equivalent to saying that only 2% get any usage-derived highlighting (Harvard have some usage information 11.5% of all items but many of these are aggregated into the score 1 bin).
  3. Scores have been normalized so that about 140 items (0.001% of all items) are in each of the top scores (100, 99, 98...), rising slowly to 277 items (0.002% of all items) with score 50, and about 1000 items with score 25.
  
I calculated an initial score for Cornell data using a similar normalization approach to the Harvard data: putting an equal number of bins in each score 2-100, with the rest in score 1. The raw scoring algorithm was very simple: `browses`*1 + `charges`*3 + `circulations`*5 (which has a double counting of ciculations that I didn't notice at the time because they are also present as a charge count). The resulting distribution is in `cornell_stackscore_distribution_2015-06-25.dat` and below is a comparison of the Cornell and Harvard distributions (also [PDF](compare_stackscore_distributions_2015-06-25.pdf)):

![Initial comparison of the Cornell and Harvard StackScore distributions](compare_stackscore_distributions_2015-06-25.png)

Features from the comparison between Cornell and Harvard data:

  1. The Cornell data has a _thinner_ tail at high stackscore than the Harvard data. This is because the method of grouping is sensitive to the number of different raw scores -- with fewer raw scores there are fewer single-item high scores to group into high stack-score for the Cornell data.
  2. The Cornell data has a smaller fraction of items with no usage information, and hence stackcore 1, than the Harvard data. In a system such as [StackLife](http://stacklife.law.harvard.edu/) there is essentially no difference shown in the UI between stackscore 1 and stackscore 2. However, if we had a system where search result ordering was adjusted based on stackscore, then a search with no high-scoring results could have result order significantly affected by the differences in low stackscores (as almost 93% of Cornell items have stackscore 1 or 2 in the above).

Without other information to indicate how the distributions should differ between institutions, it seems likely (unproven!) that the most sharable and mixable data would result from each instition's StackScores having a similar disrtibution. I thus adjusted the code to take a reference distribution (derived from the Harvard distribution) as the 'gold standard' and to bin new data according to that. Of course, we could use any other chosen distribution.

Also, in order to do something that uses the circulation date to provide a smooth score increase for more recent use I have applied an exponential decay to circulation data scoring so the overall algorithm is now:

```
    score = charges * charge_weight +
            browses * browse_weight +
            sum_over_all_circ_trans( circ_weight + 0.5 ^ (circ_trans_age / circ_halflife) )
```

This means that a circulation that happens today will score (`charge_weight`+`circ_weight`) whereas on the happened `circ_halflife` ago will score (`charge_weight`+0.5*`circ_weight`). An old circulation event that is recored only in the charge counts will score just `charge_weight`. I have no principled way to adjust the weights and halflife, for now they are:

```
    charge_weight = 2 
    browse_weight = 1
    circ_weight = 2
    circ_halflife =  5 years
```

With these things built in, I did a new run to get the newly normalized stackscore distribution (can also get the actual StackScore dump with `--stackscores=stackscores.dat.gz`). To account for the fact that not all items have usage data, the parameter `--total-bib-ids=7068205` is used to set the known total number of `bib_ids` (taken from a dump earlier in the year, a little out of date):

```
simeon@RottenApple ld4l-cul-usage>time ./parse_cul_usage_data.py -v --charge-and-browse=/cul/data/voyager/charge-and-browse-counts.txt.gz --circ-trans=/cul/data/voyager/circ_trans.txt.gz --total-bib-ids=7068205
INFO:root:STARTED at 2015-07-20 16:29:28.293820
INFO:root:Reading charge and browse counts from /cul/data/voyager/charge-and-browse-counts.txt.gz
WARNING:root:[/cul/data/voyager/charge-and-browse-counts.txt.gz line 410101] Ignoring "445360   0 0"] need more than 3 values to unpack
WARNING:root:[/cul/data/voyager/charge-and-browse-counts.txt.gz line 4886959] Ignoring "9087718   0 0"] need more than 3 values to unpack
WARNING:root:[/cul/data/voyager/charge-and-browse-counts.txt.gz line 5700896] Ignoring "6046736   0 0"] need more than 3 values to unpack
WARNING:root:[/cul/data/voyager/charge-and-browse-counts.txt.gz line 6620231] Ignoring "7090686   0 0"] need more than 3 values to unpack
WARNING:root:[/cul/data/voyager/charge-and-browse-counts.txt.gz line 6762032] Ignoring "7216658 5152672 73  3559873"] excessive browse count: 3559873 for bib_id=5152672
INFO:root:Found 5257154 bib_ids in charge and browse data
INFO:root:Reading circulation transactions from /cul/data/voyager/circ_trans.txt.gz
INFO:root:Found 1736038 bib_ids in circulation and transaction data
INFO:root:Writing summary distribution to raw_scores_dist.dat...
INFO:root:Reading reference distribution from reference_dist.dat...
INFO:root:Have 954836 distinct raw scores from 2345788 items
INFO:root:Writing distribution to stackscore_dist.dat...
INFO:root:FINISHED at 2015-07-20 16:34:22.236372

real  4m54.581s
user  4m52.153s
sys 0m1.751s
simeon@RottenApple ld4l-cul-usage>cp stackscore_dist.dat analysis/cornell_stackscore_distribution_2015-07-20.dat 
```

The resulting distribution is in `cornell_stackscore_distribution_2015-07-20.dat` and below is a comparison of the Cornell and Harvard distributions (also [PDF](compare_stackscore_distributions_2015-07-20.pdf)). We see that the Cornell distribution even recreates the noise the in the Harvard distribution. Presumably if we move forward with the creation of sharable data we should both attempt to match some agreed distribution.

![Comparison of the Cornell and Harvard StackScore distributions with Cornell data normalized to match Harvard data.](compare_stackscore_distributions_2015-07-20.png)

## Are the StackScores any good?

The current calculation uses somewhat arbitrary scaling of availale data. How can we tell whether it is likely to be of any use? How we can know how to improve it? A few thoughts:

  * Discuss Harvard experience with [StackLife](http://stacklife.law.harvard.edu/) and feedback on that
  * Appropriate scoring probably depends on how the score is used. How would "appropriate" differ between StackLife and, say, weighting in a search?
  * A simple way to get some sort of "validation" for the items with high StackScores would be to show the items to librarians or other subject experts. A slightly more sophisticated way to question would be to ask or review comparitive StackScores between items in a particular subject area. Neither of these would get at the question of items that don't have high StackScore but perhaps would be expected to. Once could ask experts for items they thing should be highly ranked and then see where they sit (might get to work/manifestation issues here).

## Possible additional sources of data not currently used

  * Course reserves
  * Number of holdings for a given item
  * Number of locations with a holding of a given item (can get this from item records where we probably want the `perm_loc` code mapped to location, will be null/empty for electronic items). Locations include the annex -- should this perhaps _reduce_ the score for an item? Recorded in field [851](http://www.oclc.org/bibformats/en/8xx/851.html) of the holdings records.
  * Circulation data stored includes the patron group which indicates either borrower status (faculty, undergraduate, etc.) or that the circulation event was via BorrowDirect or ILL.
  * Circulation data stored includes the loan period which could be used to deduce the whether it was short-term loan, etc. 

## Work level StackScore?

The above analysis and the Harvard work computes StackScore at the level of catalog bib records. If, as part of LD4L, we use OCLC works data to present views based on aggregate works, how should we combine the StackScore data from included expressions?
  
