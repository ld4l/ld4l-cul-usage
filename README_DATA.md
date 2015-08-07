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

## Circulation transactions

The circulation dump contains lines which have `circ_id`, `item_id`, `bib_id`, `date`, one for every circulation transaction since the Voyager system was implemented. Notes:

  * Some lines are missing the `item_id` and/or `bib_id`. These lines are ignored in the current analysis because we want only events that can be tied to a current `bib_id`. Lines without a `bib_id` may be items that have been removed, or faculty copies put on reserve for which stub bib record was created and then removed.
  * The circulation data stored in Voyager includes checkouts of laptops and other equipment. However, this will be filtered out because it will not match any `bib_id`.
  * The circulation data stored in Voyager includes a parton group which is not included in the date dumped. There are 20 different patron groups, one of which is recorded for each circulation transaction. For local circulations the groups are mostly based on borrower status such as undergraduate, graduate, faculty and staff, but there are aso group codes for Borrow Direct and ILL. Of the ~10M transactions recorded, about 43% are undergraduate, 25% graduate, 5% ILL, and 1.2% Borrow Direct.
  * The circulation data stored in Voyager includes a loan interval which is not present in the data dumped. The loan interval could be used to deduce the loan type (short term etc.).
