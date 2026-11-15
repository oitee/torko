You get the groups of points that members of the Lok Sabha, the lower house of the Parliament of India, made on one side of one bill. A first pass made the groups. Each group has a number, a label, the count of points, and the text of its points. Every group is on the same side: all for the bill, or all against it.

The first pass made too many groups. Some groups give the same reason in other words. Find the groups that give the same reason and join them.

Answer with JSON only, in this form:

{"joins": [{"groups": [1, 7, 12], "label": "short neutral label"}]}

Rules:

1. Join two groups when a member who reads both labels sees one reason. For example, "Delays women's reservation by linking it to delimitation" and "Holds women's reservation hostage to delimitation" give one reason.
2. A group that adds a detail to a reason joins that reason, when the detail is not a separate reason. For example, "Links women's reservation to delimitation at the discretion of the executive" joins "Delays women's reservation by linking it to delimitation".
3. Do not join two groups on the same topic with different reasons. For example, "Reduces the seats of southern states" and "Penalizes states that controlled population growth" are about the same states, but they are two reasons. "Gives no sub-quota for OBC women" and "Gives no sub-quota for SC and ST women" are two reasons, because they name different groups of people.
4. Each group number appears in at most one join. A join has at least two groups. Leave out a group that joins no other group.
5. The label of a join says the shared reason in at most 12 words. Write it as a statement about what the bill does or fails to do, with the bill as the subject that is not written. The label is neutral. Do not name a member or a party. Do not add a fact that no point gives.
6. If no groups give the same reason, answer {"joins": []}.
