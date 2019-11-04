import re


def formatter(terms=[]):
    """Format the terms to avoid possible issues when compiling the regExpression

    :param terms: 'list' string terms to be reformated
    :return: 'list' reformatted terms
    """
    replace_terms = [['.','\.'],  # '.' should be literal
                     ['$','\$'],  # '$' should be literal
                     ['!','\!'],  # '!' should be literal
                     ['[','\['],  # '!' should be literal
                     ['(','\('],  # '!' should be literal
                     [')','\)'],  # '!' should be literal
                     ['<','\<'],  # '!' should be literal
                     ['>','\>'],  # '!' should be literal
                     ['*','.*']]  # '*' should be wildcard
    results = []
    for term in terms:
        for old, new in replace_terms:
            if term == '\\':
                continue
            term = term.replace(old, new)
        results.append(term)
    return results


def precompile(includes=[], excludes=[], required=[], starts=[], ends=[],
               unified_excludes=False, case_sensitive=False, format_terms=True):
    """Compile the regExpression for the terms

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
    # compare all the terms and make sure they're of similar types
    is_regex = None
    for term in includes + excludes + required + starts + ends:
        # store type of first entry
        string_check = isinstance(term, str)
        if is_regex is None:
            is_regex = not string_check
            continue
        # there should not be a mixture of strings and regExpresions
        if string_check == is_regex:
            msg = 'Mix of regExpressions and str, cannot reliably declare terms'
            raise ValueError(msg)

    includesREGs, excludesREGs, requiredREGs, startsREGs, endsREGs = [], [], [], [], []
    if is_regex is True:
        results = [includesREGs, excludesREGs, requiredREGs, startsREGs, endsREGs]
        terms = [list(ls) for ls in (includes, excludes, required, starts, ends)]
        # store the vars onto class
        for typeList, items in zip(results, terms):
            typeList.clear()
            typeList.extend(items)
    else:
        # update the characters in terms to match correct formatting for regexpressions
        if format_terms:
            includes = formatter(includes)
            excludes = formatter(excludes)
            required = formatter(required)
            starts = formatter(starts)
            ends = formatter(ends)

        # collect the case_sensitive flag
        caseFlag = 0
        if not case_sensitive:
            caseFlag = re.IGNORECASE
        # precompile the  regexpressions
        # required
        if required:
            requiredREGs = [re.compile(t, caseFlag) for t in required]
        # exclusions
        if excludes:
            if not unified_excludes:
                excludesREGs = [re.compile(t, caseFlag) for t in excludes]
            else:
                term = '|'.join( excludes )
                excludesREGs.append(re.compile(term, caseFlag))
        # includes
        if includes:
            term = '|'.join( includes )
            includesREGs.append(re.compile(term, caseFlag))
        # starts
        if starts:
            term = '^({})'.format('|'.join(starts))
            startsREGs.append(re.compile(term, caseFlag))
        # ends
        if ends:
            term = '({})$'.format('|'.join(ends))
            endsREGs.append(re.compile(term, caseFlag))
    results = [includesREGs, excludesREGs, requiredREGs, startsREGs, endsREGs]
    return results
