"""
Coherence and presence tests on wanted properties
"""


class Test(object):
    """
    generic test for a decision to pass
    """

    ignore_flags = []
    valid = True
    explanation = ""

    def bypass_test(self, results):
        flags = results["flags"]
        for i in self.__class__.ignore_flags:
            if i in flags:
                return True
        return False

    def apply_to_results(self, results, loud=False):
        if not self.bypass_test(results):
            try:
                self.run(results)
            except AssertionError:
                if loud:
                    raise AssertionError(self.__class__.explanation)
                else:
                    return self.__class__.explanation

    def run(self, results):
        """
        return true if test is passed
        """
        return False


def run_tests(results):
    """
    apply all tests and retrieve failures
    """
    failures = []
    count = 0
    for test in valid_tests:
        if test.valid:
            count += 1
            result = test().apply_to_results(results)
            if result:
                failures.append(result)
    if failures:
        print(results)
        print("{0} tests failed".format(len(failures)))
        for f in failures:
            print(f)
    else:
        print("{0} Tests passed.".format(count))
    return failures


class StartDate(Test):
    ignore_flags = ["ignore_processing", "no_start_date"]
    explanation = "Missing start date"

    def run(self, results):
        assert results["start_date"]


class ICODate(Test):
    # currently ignoring this
    ignore_flags = ["ignore_processing", "no_ico"]
    explanation = "Missing ico date"
    valid = False

    def run(self, results):
        assert results["ico_date"]


class DateOrderICO(Test):
    # currently ignoring this
    ignore_flags = [
        "ignore_processing",
    ]
    explanation = "Request passed before to ICO before made"

    def run(self, results):
        if results["ico_date"] and results["start_date"]:
            assert results["start_date"] < results["ico_date"]


# count split into is equal to, and much lower than? some data errors


class NoIRDate(Test):
    ignore_flags = ["ignore_processing", "no_ir_date"]
    explanation = "No review date, but IR mentioned"

    def run(self, results):
        if "ir_mention" in results["flags"]:
            assert results["review_date"] or results["review_reply_date"]


class IRDateOrder(Test):
    ignore_flags = ["ignore_processing", "no_ir_date"]
    explanation = "Review cannot be sent after received"

    def run(self, results):
        if results["review_date"] and results["review_reply_date"]:
            assert results["review_date"] < results["review_reply_date"]


class SubstativeReply(Test):
    ignore_flags = ["does_not_require", "new_response", "steps_to_comply"]
    explanation = "SR mentioned, but not flagged"

    def run(self, results):
        flags = results["flags"]
        if "sr_mention" in flags and "s10_mention" in flags:
            assert (
                "substantive_response" in flags
                or "provided_substantive_response" in flags
            )


valid_tests = [x for x in Test.__subclasses__() if x.valid]
