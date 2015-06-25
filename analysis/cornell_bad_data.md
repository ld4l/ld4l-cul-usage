# BAD DATA

Bad data found during analysis

## Excessive browse count

In the file of historical charge counts and browse counts there are a number of items with a thousand or more charge and browse counts, a few instances of counts of several thousand. There is one obviously erroneous case with a browse count of 3.5 million:

`item_id`=7216658 `bib_id`=5152672 has a browse count of 3559873, a for orders of magniture wrong! This is <https://newcatalog.library.cornell.edu/catalog/5152672>.

Have set code to ignore any entry with a charge or browse count > 10000.

