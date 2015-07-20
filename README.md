# ld4l-cul-usage

Scripts for analysis of anonymous Cornell University Library (CUL) usage data and compilation of a normalized StackScore. The goal of this work is to experiment with cross-institutional use of usage data, as an extension of the StackScore created by the Harvard [StackLife](http://stacklife.harvard.edu/) project. Every item is assigned a score representing community usage on a scale of 1 to 100. How useful is such a score? How should such a score be computed from available data? What are the requirements for the combination of items from multiple institutions with locally computed scores?

## Privacy

The [CUL privacy policy](https://www.library.cornell.edu/privacy) and associated [practices](https://www.library.cornell.edu/practices) describe the care taken remove personally identifiable information from circulation records as soon as possible:

> The Library respects the privacy of all borrowers of library materials. The Library will not reveal the names of individual borrowers nor reveal what books are, or have been, charged to any individual except as required by law.  Only staff members who have a functional need to view circulation data can view who has borrowed a book.
> 
> The Library seeks to protect user privacy by purging borrowing records as soon as possible.  In general, the link connecting a patron with a borrowed item is broken once the item is returned.  The exception is when a bill for the item is generated.  In that case, the information on who borrowed the item is retained indefinitely in our system.  For security reasons, records of who requested items from the Library’s special collections are also retained indefinitely.

Thus the raw data we have available is already anonymous. This anonymous raw data might still allow derivation of some co-usage information but we have no plans to attempt this for the LD4L project.

## CUL usage data

We have three types of local usage data available:

  1. circulation (charge) counts, a single number per `item_id` which is mapped to a `bib_id`, which includes data imported from the previous library management system (Notis) around 2000.
  2. browse counts, a single number per `item_id` which is mapped to a `bib_id`, which includes data imported from the previous library management system (Notis) around 2000. The counts are unevenly accurate across items because they depend on practices that have varied across libraries and over time.
  3. the circulation transaction archive which provides dated records for each circulation event for the life of the current library management system (Voyager, since around 2000). The data records a set of dates for each per `item_id` which is mapped to a `bib_id`. Each circulation event is reflected in an increment in the correspondig charge count so this data adds only time information. We might want to use this to get a time-weighted (more recent use counts for more?) or time-cutoff (say use in last X years?) usage score. 

In all cases we will aggregate data at the `bib_id` rather than maintaining any of the information about individual copies (`item_id`). It may also be useful or necessary to aggregate counts or derived scores at the work level.

  * [Data dumps and formats](README_DATA.md)
  * [Analysis](analysis/README.md)
