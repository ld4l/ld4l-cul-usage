# Privacy issues

A key motivation for use of a normalized and coarse grained StackScore is the preservation of the privacy of borrowers and readers of library materials, while still allowing usage information to be of benefit.

## CUL privacy policy and practices

The [CUL privacy policy](https://www.library.cornell.edu/privacy) and associated [practices](https://www.library.cornell.edu/practices) describe the care taken remove personally identifiable information from circulation records as soon as possible:

> The Library respects the privacy of all borrowers of library materials. The Library will not reveal the names of individual borrowers nor reveal what books are, or have been, charged to any individual except as required by law.  Only staff members who have a functional need to view circulation data can view who has borrowed a book.
> 
> The Library seeks to protect user privacy by purging borrowing records as soon as possible.  In general, the link connecting a patron with a borrowed item is broken once the item is returned.  The exception is when a bill for the item is generated.  In that case, the information on who borrowed the item is retained indefinitely in our system.  For security reasons, records of who requested items from the Library’s special collections are also retained indefinitely.

## Anonymity

Almost all of the raw data that CUL collects is already anonymous. To ensure that there can be no leakage of user identity in the case of records that do have borrower identity information, the data dumps extracted to calculate the StackScore should not include any identity information

## Co-usage

The anonymous raw data might allow derivation of some co-usage information. We have no plans to attempt to extract or use such information in the LD4L project. However, we should be careful that such information is not accidentally leaked.

### Co-usage leakage via real-time updates

*Scenerio*: If circulation events were provided or created updates in real-time or near real-time then it , and the StackScores published will obscure it by their large granularity and periodic updates.

*Mitigation*: Our plan is to update StackScore values only periodically, likely weekly or monthly. Circulation events are recorded only at day granularity (date without time). Even if we were to update scores on a daily basis, individual co-usage events would be mixed with the whole event over the whole day.

### Co-usage leakage via correlated score changes

*Scenario*: If circulation events were recorded with high time precision then co-circulation events might show up as correlated score changes.

*Mitigation*: Circulation events are recorded only at day granularity (date without time). Additionally, most subtle differences in raw score (perhaps based on an exponential decay from checkout time) are obscured by the very coarse binning of raw scores into the normalized 1--100 StackScore.
