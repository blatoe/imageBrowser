import re

import regex


def fragment(terms=[], splits=[], separates=[], excludes=[], camelCase=False,
             clean=False):
    """Given a list of terms, split and seperate the strings apart with by the
     given inputs; returning a list of deconstructed terms.

    :param terms: 'list' Strings that will be deconstructed into smaller parts
    :param splits: 'list' Split the terms apart with by the given strings
    :param separates: 'list' Section off and keep the parts of terms that match
    :param excludes: 'list' Any parts matching these terms will be disregarded
    :param camelCase: 'bool' Section off a term by capitalization that occurs
    :param clean: 'bool' Format the splits and separates terms to avoid possible
     issues when compiling the regExpression
    :return: 'list' all terms that remain after splitting and partitioning
    """
    # validate and format the inputs
    if not terms and (not splits and not separates):
        msg = 'No terms, splitters, or separators given to fragment'
        return []
    if isinstance(terms, str):
        terms = [terms]
    # sort the separates in reverse order to avoid partitioning terms too soon.
    separates = sorted(separates, reverse=True)
    if clean:
        splits = regex.formatter(splits)
        if ' ' not in splits:
            splits += ' '
        separates = regex.formatter(separates)
    results = list(terms)
    # split
    for split in splits:
        ls = []
        for term in results:
            data = re.split(split, term)
            ls.extend([t for t in data if t])
        results = ls
    # separate
    for separate in separates:
        pattern = '(.*)({})(.*)'.format(separate)
        ls = []
        for term in results:
            match = re.search(pattern, term)
            if match:
                ls.extend([t for t in match.groups() if t])
                continue
            ls.append(term)
        results = ls
    # camelCase
    if camelCase:
        ls = []
        for term in results:
            match = re.findall('^[a-z]+|[A-Z][^A-Z]*', term)
            if match:
                ls.extend(match)
                continue
            ls.append(term)
        results = ls
    # excludes
    results = filter(results, excludes=excludes)
    return results


def grouping(items=[], searchTerms=[]):
    """Sort the list of items into separate groups that match a set of
     searchTerms. An item will only be placed into the first group it matches.
     Any items not matched are placed into an extra group.

    :param items: 'list' Terms to be evaluated and separated
    :param searchTerms: 'list' sets of terms to be used in collecting terms
    :return: 'list' sets of terms grouped together based on the inputs
    """
    inclusionTerms = searchTerms
    if isinstance(searchTerms, str):
        inclusionTerms = [[searchTerms]]
    if not isinstance(inclusionTerms[-1], list):
        inclusionTerms = [inclusionTerms]
    flatTerms = flatten(inclusionTerms)
    results = [[] for i in inclusionTerms]
    if not items or not searchTerms:
        # raise ValueError('No items or searchTerms given')
        return results
    unmatched = []
    for item in items:
        item = item.strip()
        while item.endswith(' '):
            item = item[:-1]
        if item in flatTerms:
            unmatched.append(item)
            continue
        unprocessed = True
        # look for items starting with the filterPatterns
        # to determine the item type
        for itemList, patterns in zip(results, searchTerms):
            for p in patterns:
                if not p or len(p) > 1:
                    continue
                if item.startswith(p):
                    unprocessed = False
                    itemList.append(item[1:])
        # if the item is valid and could not be determined
        # it's handled as a 'OR' search item
        if item and unprocessed:
            unmatched.append(item)
    if unmatched:
        results.append(unmatched)
    return results


def flatten(data):
    """Unpack sets of nested lists into a single list

    :param data: 'list' sets of nested lists to unpack and flatten
    :return: 'list' single flattened list of all items in the heirachy
    """
    results = []
    for item in data:
        if isinstance(item, list) or isinstance(item, tuple):
            for i in flatten(item):
                results.append(i)
        else:
            results.append(item)
    return results


def filter(items=[], includes=[], excludes=[], required=[], starts=[],
           ends=[], unified_excludes=False, case_sensitive=False):
    """All items that fit the different criteria of matching and excluding
     the different terms.

    :param items: 'list' string terms that will be evaluated
    :param includes: 'list' item will be valid if they contain any terms
        from this list
    :param excludes: 'list' item will not be valid if they contain any terms
        from this list
    :param required: 'list' item will only be valid if they all terms from
        this list
    :param starts: 'list' item will be valid if they start with any terms
        from this list
    :param ends: 'list' item will be valid if they end with any terms
        from this list
    :param unified_excludes: 'bool' combines all exclude terms so that all
        must be valid for a match to be detected
    :param case_sensitive: 'bool' Case sensitvity will be respected in determining
        if item is valid
    :return: 'list' The terms matching the filter parameters
    """
    results = FilterList().run(items=items, includes=includes, excludes=excludes,
                               required=required, starts=starts, ends=ends,
                               unified_excludes=unified_excludes,
                               case_sensitive=case_sensitive)
    return results


class FilterList(object):
    def __init__(self, items=[], includes=[], excludes=[], required=[],
                 starts=[], ends=[], unified_excludes=False, case_sensitive=False):
        """All items that fit the different criteria of matching and excluding
         the different terms.

        :param items: 'list' string terms that will be evaluated
        :param includes: 'list' item will be valid if they contain any terms
            from this list
        :param excludes: 'list' item will not be valid if they contain any terms
            from this list
        :param required: 'list' item will only be valid if they all terms from
            this list
        :param starts: 'list' item will be valid if they start with any terms
            from this list
        :param ends: 'list' item will be valid if they end with any terms
            from this list
        :param unified_excludes: 'bool' combines all exclude terms so that all
            must be valid for a match to be detected
        :param case_sensitive: 'bool' Case sensitivity will be respected in
            determining if item is valid
        :return: 'list' The terms matching the filter parameters
        """
        self._items = items
        self._includes = includes
        self._excludes = excludes
        self._required = required
        self._starts = starts
        self._ends = ends
        self._unified_excludes = unified_excludes
        self._case_sensitive = case_sensitive
        self._indices = {}

        self._includesREGs = []
        self._excludesREGs = []
        self._requiredREGs = []
        self._startsREGs = []
        self._endsREGs = []

        self._data = []
        # precompile the regexpression if any terms were passed in
        if includes + excludes + required + starts + ends:
            self.regFilters()

    # --------------------------------------------------------------------------
    def regFilters(self, includes=None, excludes=None, required=None,
                   starts=None, ends=None, unified_excludes=None,
                   case_sensitive=None, format_terms=True):
        """Compile and store the regExperssion for the given or cached terms
        All items that fit the different criteria of matching and excluding
         the different terms.

        :param includes: 'list' item will be valid if they contain any terms
            from this list
        :param excludes: 'list' item will not be valid if they contain any terms
            from this list
        :param required: 'list' item will only be valid if they all terms from
            this list
        :param starts: 'list' item will be valid if they start with any terms
            from this list
        :param ends: 'list' item will be valid if they end with any terms
            from this list
        :param unified_excludes: 'bool' combines all exclude terms so that all
            must be valid for a match to be detected
        :param case_sensitive: 'bool' Case sensitvity will be respected in
            determining if item is valid
        :param format_terms: 'bool' Format the terms to avoid possible issues
            when compiling the regExpression
        :return: 'list' precompiled regExpressions"""
        # check if we can pull from the class vars if no input given
        mapping = {'includes': includes,
                   'excludes': excludes,
                   'required': required,
                   'starts': starts,
                   'ends': ends,
                   'unified_excludes': unified_excludes,
                   'case_sensitive': case_sensitive}
        for term, var in mapping.items():
            if var is not None:
                # term is passed in, set on class
                setattr(self, '_{}'.format(term), var)
            else:
                # term not given, pull from class
                exec('{0} = self._{0}'.format(term))
        # compare all the terms and make sure they're of similar types
        is_regexpression = None
        for term in includes + excludes + required + starts + ends:
            # store type of first entry
            stringCheck = isinstance(term, str)
            if is_regexpression is None:
                is_regexpression = not stringCheck
                continue
            # there should not be a mixture of strings and regExpressions
            if stringCheck == is_regexpression:
                msg = 'Mixed regExpressions and str, cannot reliably declare terms'
                raise Exception(msg)

        includesREGs, excludesREGs, requiredREGs, startsREGs, endsREGs = [], [], [], [], []
        if is_regexpression is True:
            # store the vars onto class
            varTerms = 'includes excludes required starts ends'
            for var in varTerms.split():
                exec('{0}REGs = {0}'.format(var))
        else:
            # precompile reg expressions to speed up operations
            regs = regex.precompile(includes=includes, excludes=excludes,
                                    required=required, starts=starts, ends=ends,
                                    unified_excludes=unified_excludes,
                                    case_sensitive=case_sensitive,
                                    format_terms=format_terms)
            includesREGs, excludesREGs, requiredREGs, startsREGs, endsREGs = regs

        # store the vars onto the class
        mapping = {'includes': includesREGs,
                   'excludes': excludesREGs,
                   'required': requiredREGs,
                   'starts': startsREGs,
                   'ends': endsREGs}
        for term, regs in mapping.items():
            setattr(self, '_{}REGs'.format(term), regs)
        return [includesREGs, excludesREGs, requiredREGs, startsREGs, endsREGs]

    # --------------------------------------------------------------------------
    def run(self, items=None, includes=None, excludes=None, required=None, starts=None,
            ends=None, unified_excludes=None, case_sensitive=None):
        """All items that fit the different criteria of matching and excluding
         the different terms.

        :param items: 'list' string terms that will be evaluated
        :param includes: 'list' item will be valid if they contain any terms
            from this list
        :param excludes: 'list' item will not be valid if they contain any terms
            from this list
        :param required: 'list' item will only be valid if they all terms from
            this list
        :param starts: 'list' item will be valid if they start with any terms
            from this list
        :param ends: 'list' item will be valid if they end with any terms
            from this list
        :param unified_excludes: 'bool' combines all exclude terms so that all
            must be valid for a match to be detected
        :param case_sensitive: 'bool' Casesensitvity will be respected in determining
            if item is valid
        :return: 'list' The terms matching the filter parameters
        """
        # gather the regExpressions from the class
        includesREGs = self._includesREGs
        excludesREGs = self._excludesREGs
        requiredREGs = self._requiredREGs
        startsREGs = self._startsREGs
        endsREGs = self._endsREGs
        givenTerms = [includes, excludes, required, starts, ends]
        storedTerms = [self._includes, self._excludes, self._required, self._starts, self._ends]
        termsCheck = [x for x in givenTerms if x is not None]
        # check if given terms are valid and regex need to be recollected
        if termsCheck and givenTerms != storedTerms:
            varTerms = 'includes excludes required starts ends'
            for var in varTerms.split():
                exec('if {0} is None: {0} = []'.format(var))
            filters = self.regFilters(includes, excludes, required, starts,
                                      ends, unified_excludes, case_sensitive)
            includesREGs, excludesREGs, requiredREGs, startsREGs, endsREGs = filters
        # check if regExpressions are valid
        if None in [includesREGs, excludesREGs, requiredREGs, startsREGs, endsREGs]:
            t = 'search:\t{}\nexclude:\t{}\nrequired:\t{}\nstarts:\t{}\nends:\t{}'.format(*givenTerms)
            print('Cannot handle regExpressions as None:'+t)
        # collect items to evalate
        if items is None:
            items = self._items
        # filter the search, exclusion, required terms from the search list
        self._data = []
        self._indices = {}
        for i, item in enumerate(items):
            itemString = str(item)
            valid = True
            # required, starts, ends
            for r in requiredREGs + startsREGs + endsREGs:
                if not r.search(itemString):
                    valid = False
                    break
            if not valid:
                continue
            # exclusions
            for r in excludesREGs:
                if r.search(itemString):
                    valid = False
                    break
            if not valid:
                continue
            # includes
            for c, r in enumerate(includesREGs):
                if not r.search(itemString):
                    valid = False
                    break
            if valid:
                self._indices[i] = item
                self._data.append(item)
        return self._data