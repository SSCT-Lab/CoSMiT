# New protocol assertion continuation; see registration.json.
def check(self, expected, actual):
    self.assertEqual(expected.shape, actual.shape)
