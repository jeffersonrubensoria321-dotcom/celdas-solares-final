"""Pruebas reales de reejecucion y estado de Streamlit (sin navegador)."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest


class InterfaceTests(unittest.TestCase):
    def test_controls_and_shared_state(self):
        app = AppTest.from_file(str(Path(__file__).with_name('app.py')), default_timeout=40).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.tabs), 4)
        self.assertEqual(app.session_state['temp'], 35.0)
        self.assertIn('S = 1', app.sidebar.header[0].value)
        app.slider(key='eg').set_value(1.7).run()
        self.assertEqual(len(app.exception), 0)
        app.slider(key='temp').set_value(75.0).run()
        self.assertEqual(len(app.exception), 0)
        app.checkbox(key='loss6').uncheck().run()
        self.assertEqual(len(app.exception), 0)
        app.sidebar.button[1].click().run()
        self.assertEqual(app.session_state['eg'], 1.12)
        self.assertFalse(app.session_state['loss7'])
        self.assertEqual(len(app.exception), 0)
        app.sidebar.button[0].click().run()
        self.assertEqual(app.session_state['temp'], 35.0)
        self.assertTrue(app.session_state['loss7'])
        self.assertEqual(len(app.exception), 0)


if __name__ == '__main__':
    unittest.main()
