# Copyright 2017, Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__all__ = ['singularize', 'pluralize', 'article']


def singularize(word):
    if word.endswith('ies'):
        return word[:-len('ies')] + 'y'
    elif word.endswith('s'):
        return word[:-1]
    else:
        return word


def pluralize(kind):
    if kind == 'inventory':
        return 'inventories'
    elif kind == 'workflow':
        return 'workflow_job_templates'
    else:
        return '%ss' % kind


def starts_with_vowel(word):
    vowels = ('a', 'e', 'i', 'o', 'u')
    return word[0].lower().startswith(vowels)


def article(word):
    if starts_with_vowel(word) and not word.startswith('u'):
        return 'an'
    else:
        return 'a'
