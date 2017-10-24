Versioning of tower-cli
=======================

Tower-CLI is a command-line interface and python library to interact with
Ansible Tower and AWX. Only versions of tower-cli can successfully
interact with only a certain subset of versions of Ansible Tower or AWX,
and this document is meant to outline the policy.

API Versions
------------

Ansible Tower and AWX communicate with clients through a particular API
version, so that each version forms a stable API for Ansible Tower.
Each version of tower-cli also has a corresponding API version.

Supported Versions with Ansible Tower
-------------------------------------

The following table summarizes the policy of supported versions.

=============  =============  ====================
   tower-cli    API version    Tower version 
=============  =============  ====================
3.1.x             v1           3.2.x and earlier
current           v2           3.2.x and later
=============  =============  ====================

This means that the release series 3.1.x is still open for fixes in
order to support communication with the v1 API and all Tower versions
that support that. Many elements of functionality are removed in the
transition to v2, so they are no longer carried with the current tower-cli
version.

Policy with AWX Versions
------------------------

Compatibility between tower-cli and the AWX project is only considered
for the most recent development version of tower-cli and most recent
version of AWX.
