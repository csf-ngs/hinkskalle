---
title: Quotas
weight: 3
---

User/Group Quotas

<!--more-->

You can limit the amount of space your users can take up by imposing quotas.

## Configuration

Default values for quotas can be set in `config.json` or environment variables:

- `DEFAULT_USER_QUOTA` - preset value for new users (also self-registration, if enabled)
- `DEFAULT_GROUP_QUOTA` - preset value for new groups

A value of 0 means unlimited.

Refer to the [configuration section](./configuration.md) for details.

## User Quotas

We sum the sizes all containers uploaded by a user with these rules:

1. Valid containers (state must be `uploaded`, partial or broken pushes do not count towards the quota)
2. Distinct containers by the same user count only once, so that multiple pushes (e.g. reuse container in different collections, push to a group) are not penalized
3. If the same container (by checksum) is pushed by different users, it counts once for each user

(there is a reason for 3.: which users' quota is counted (the first?), what happens if the first user deletes his container and "moving" the quota would cause a quota exceeded? etc.)

## Group Quotas

Group quotas are enforced *in addition* to user quotas and refer to:

1. The sum of sizes of valid, distinct containers for a group
2. Again, the same container (by checksum) counts once for each group it is pushed to

This means that if a user would exceed their own quota when pushing a container to a group, Hinkskalle rejects the push even if the group quota allows it.

As long as users are allowed to create groups this is the only useful way to implement user quotas (in my opinion -> please open an issue if think otherwise).

Of course this means that group quotas are not particularly useful - you might want to leave the default at 0 (=unlimited), because the size of a group is limited by their members' quotas anyways; and put quotas on individual groups in special cases as needs arise.

### Why Not Independent Group Quotas?

Reasoning: Otherwise a user could just create more groups to raise their quota. 

Potential fixes and counters:

- do not allow group creation by users (restrictive, inflexible, discourages collaboration)
- only count separate quotas if a group has >1 member (complicates rules, easily circumvented, what happens if other member leaves?)
- group quota as sum of all member quotas? sounds nice + collaborative but does not actually solve anything when you think about it. 

Maybe a future version could allow a toggle to disable group creation (e.g. if groups come from a different source like LDAP) and:

- count group containers to groups, user containers to user if group creation is disabled
- user quota for all containers uploaded by user otherwise