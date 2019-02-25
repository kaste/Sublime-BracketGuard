import sublime

from unittesting import DeferrableTestCase, AWAIT_WORKER


class TestBracketGuard(DeferrableTestCase):
    def setUp(self):
        s = sublime.load_settings("BracketGuard.sublime-settings")
        val = s.get("debounce_time")
        s.set("debounce_time", 0)
        self.addCleanup(lambda: s.set("debounce_time", val))

        self.view = sublime.active_window().new_file()

    def tearDown(self):
        if self.view:
            self.view.set_scratch(True)
            self.view.close()

    def insertCodeAndGetRegions(self, code):
        self.view.run_command("insert", {"characters": code})
        yield AWAIT_WORKER  # await modified (async) event
        yield AWAIT_WORKER  # await debouncer
        return self.view.get_regions("BracketGuardRegions")

    def testPureValidBrackets(self):
        openerRegions = yield from self.insertCodeAndGetRegions("([{}])")
        self.assertEqual(len(openerRegions), 0)

    def testValidBracketsInCode(self):
        openerRegions = yield from self.insertCodeAndGetRegions("a(bc[defg{hijkl}mn])o")
        self.assertEqual(len(openerRegions), 0)

        openerRegions = yield from self.insertCodeAndGetRegions("<a href={ url }>")
        self.assertEqual(len(openerRegions), 0)

    def testInvalidBracketsWrongCloser(self):
        bracketGuardRegions = yield from self.insertCodeAndGetRegions("({}])")

        self.assertEqual(len(bracketGuardRegions), 2)
        self.assertEqual(bracketGuardRegions[0].a, 0)
        self.assertEqual(bracketGuardRegions[1].a, 3)

    def testInvalidBracketsNoCloser(self):
        bracketGuardRegions = yield from self.insertCodeAndGetRegions("({}")

        self.assertEqual(len(bracketGuardRegions), 2)
        self.assertEqual(bracketGuardRegions[0].a, -1)
        self.assertEqual(bracketGuardRegions[1].a, 0)

    def testInvalidBracketsNoOpener(self):
        bracketGuardRegions = yield from self.insertCodeAndGetRegions("){}")

        self.assertEqual(len(bracketGuardRegions), 2)
        self.assertEqual(bracketGuardRegions[0].a, -1)
        self.assertEqual(bracketGuardRegions[1].a, 0)
