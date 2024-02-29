# Copyright 2024, Adfinis AG
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ansible.module_utils.common.locale import get_best_parsable_locale
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type

import os


DOCUMENTATION = r'''
---
module: apt_sources_facts
short_description: Set configured apt sources as facts.
description:
  - Set configured apt sources as facts.
  - Requires the C(python-apt) or C(python3-apt) package to be installed.
version_added: "1.0.2"
author: Adfinis AG (@adfinis)
options: {}
'''


EXAMPLES = r'''
- name: Populate apt sources facts
  adfinis.facts.apt_sources_facts:

- name: Print apt sources facts
  ansible.builtin.debug:
    var: ansible_facts.apt_sources
'''


RETURN = r'''
ansible_facts:
  description: Facts to add to ansible_facts about the configured apt sources.
  returned: always
  type: dict
  contains:
    apt_sources:
      description: List of all active apt sources, both from deb822 and legacy format files.
      returned: always
      type: list
      elements: dict
      sample:
        - file: /etc/apt/sources.list.d/debian.sources
          types: [deb, deb-src]
          uri: http://deb.debian.org/debian
          suites: [boomworm, bookworm_updates]
          components: [main, non-free-firmware]
          architectures: []
        - file: /etc/apt/sources.list.d/debian.sources
          types: [deb, deb-src]
          uri: http://security.debian.org/debian-security
          suites: [bookworm-security]
          components: [main, non-free-firmware]
          architectures: []
      contains:
        file:
          description: Name of the file this entry was found in.
          returned: always
          type: str
          sample: /etc/apt/sources.list
        types:
          description: Types of the entry, contains "deb", "deb-src" or both.
          returned: always
          type: list
          elements: str
          sample:
            - deb
            - deb-src
        uri:
          description: URI for the repository.
          returned: always
          type: str
          sample: http://deb.debian.org/debian
        suites:
          description: Name of the suites of the repository.
          returned: always
          type: list
          elements: str
          sample:
            - bookworm
            - bookworm-updates
        components:
          description: Enabled components of the repository.
          returned: always
          type: list
          elements: str
          sample:
            - main
            - non-free-firmware
        architectures:
          description: The entries of the "Architectures" option, if any.
          returned: always
          type: list
          elements: str
          sample:
            - amd64
'''


def main():
    module = AnsibleModule(argument_spec=dict(), supports_check_mode=True)

    # Import the sourceslist module from python-apt; emit a warning and exit if not possible.
    try:
        from aptsources.sourceslist import SourcesList, Deb822SourceEntry, SourceEntry
    except ImportError:
        warnings = [
            'adfinis.facts.apt_sources_facts was invoked on a system that is missing the python3-apt or python-apt' +
            'package.  ansible_facts.apt_sources will be empty.'
        ]
        results = dict(ansible_facts=dict(apt_sources=list()))
        module.exit_json(warnings=warnings, **results)

    # Load all .list and .sources files
    sources = SourcesList()
    for ent in os.listdir('/etc/apt/sources.list.d'):
        filename = os.path.join('/etc/apt/sources.list.d', ent)
        if ent.endswith('.sources') or ent.endswith('.list'):
            sources.load(filename)

    # Iterate both .list and .sources and convert their contents into a unified dict structure
    apt_sources = list()
    for source in sources:
        if not source.type:
            continue
        if isinstance(source, Deb822SourceEntry):
            # Don't include disabled entries
            if source.disabled:
                continue
            source_entry = dict(
                filename=source.file,
                types=source.types,
                uri=source.uri,
                suites=source.suites,
                components=source.comps,
                architectures=source.architectures
            )
        else:
            # SourcesList appears to return empty lines and comments as well
            if source.type not in ['deb', 'deb-src']:
                continue
            source_entry = dict(
                filename=source.file,
                types=[source.type],
                uri=source.uri,
                suites=[source.dist],
                components=source.comps,
                architectures=source.architectures
            )
        apt_sources.append(source_entry)
    results = dict(ansible_facts=dict(apt_sources=apt_sources))
    module.exit_json(**results)


if __name__ == '__main__':
    main()