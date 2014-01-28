def rfe_or_bug(text):
    bugs =     ['traceback',
                'error',
                'broke',
                'crash',
                'fail',
                'is skipped',
                'issue',
                'regress',
                'invalid',
                'stacktrace',
                'misbehavior',
                'bug',
                ' not ', 
                "shouldn't",
                "doesn't",
                'unexpected',
                "i think it should", "should take",
                "no longer",
                'old behavior', 'previous behavior',
                'incorrect' ]

    rfes =     ['feature',
                'feature request',
                'it would be nice',
                'i would like',
                'please add' ]

    bug_count = 0
    rfe_count = 0

    for tr in bugs:
        if tr in text.lower():
            bug_count += 1                    
    for tr in rfes:
        if tr in text.lower():
            rfe_count += 1                    

    if bug_count == 0 and rfe_count > 0:
        return "rfe"
    elif bug_count > 0 and rfe_count == 0:
        return "bug"
    else:
        import epdb; epdb.st()
        return None


