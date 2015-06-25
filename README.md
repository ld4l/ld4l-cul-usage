# ld4l-cul-usage

Scripts for analysis of anonymous CUL usage data and compilation of a normalized stack score

## Privacy

The [CUL privacy policy](https://www.library.cornell.edu/privacy) and associated [practices](https://www.library.cornell.edu/practices) describe the care taken remove personally identifiable information from circulation records as soon as possible:

> The Library respects the privacy of all borrowers of library materials. The Library will not reveal the names of individual borrowers nor reveal what books are, or have been, charged to any individual except as required by law.  Only staff members who have a functional need to view circulation data can view who has borrowed a book.
> 
> The Library seeks to protect user privacy by purging borrowing records as soon as possible.  In general, the link connecting a patron with a borrowed item is broken once the item is returned.  The exception is when a bill for the item is generated.  In that case, the information on who borrowed the item is retained indefinitely in our system.  For security reasons, records of who requested items from the Library’s special collections are also retained indefinitely.

Thus the raw data we have available is already anonymous. The raw data might allow derivation of some co-usage data but we have no plans to attempt this for the LD4L project.

## CUL usage data

We have three types of data available:

  1. historical circulation (charge) counts, a single number per `item_id` which is mapped to a `bib_id` which includes data imported from the previous library management system.
  2. histroical browse counts which are uneven because they depend on practices that have varied across libraries and over time. The data records a single number per `item_id` which is mapped to a `bib_id`.
  3. the circulation transaction archive which provides dated records for each circulation event for the life of the Voyager system. The data records a set of dates for each per `item_id` which is mapped to a `bib_id`. We might want to use this to get a time-weighted (more recent use counts for more?) or time-cutoff (say use in last X years?) usage score.

In all cases we will aggregate data at the `bib_id` rather than maintaining any of the information about individual copies (`item_id`). It may also be useful to aggregate at the work level.

### Data dumps

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
