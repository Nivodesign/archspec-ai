import json
import os
import unittest
from agent_graph import AgentState, ArchitecturalSpecParserGraph

class TestArchSpecFlow(unittest.TestCase):
    def setUp(self):
        self.db_path = os.path.join(os.path.dirname(__file__), "vendors_db.json")
        self.dummy_image = os.path.join(os.path.dirname(__file__), "test_spec_img.png")
        with open(self.dummy_image, "w") as f:
            f.write("dummy")

    def tearDown(self):
        if os.path.exists(self.dummy_image):
            os.remove(self.dummy_image)

    def test_database_structure(self):
        self.assertTrue(os.path.exists(self.db_path), "vendors_db.json should exist")
        with open(self.db_path, "r") as f:
            db = json.load(f)
            
        self.assertIn("material_matrix", db)
        self.assertIn("builders", db)
        
        # Check all 26 categories are covered
        categories = db["material_matrix"]
        self.assertEqual(len(categories), 26, "Should cover exactly 26 sub-categories")
        
        # Check builders exist
        self.assertGreater(len(db["builders"]), 0)

    def test_graph_flow_exterior(self):
        # Step 1: Initialize
        state = AgentState(
            project_id="test-proj-ext",
            scope="Exterior",
            area=2000.0,
            image_path=self.dummy_image
        )
        self.assertEqual(state.status, "START")
        
        # Step 2: Run Vision & Procurement (this should auto-run and pause)
        graph = ArchitecturalSpecParserGraph()
        state = graph.run_next(state)
        
        self.assertEqual(state.status, "PAUSED")
        self.assertEqual(len(state.detected_materials), 6, "Exterior should detect 6 categories")
        
        # Verify pricing options exist for each
        for mat in state.detected_materials:
            self.assertIn(mat["category"], state.pricing_matrix)
            pricing = state.pricing_matrix[mat["category"]]
            self.assertIn("Standard", pricing)
            self.assertIn("Mid-Range", pricing)
            self.assertIn("Premium", pricing)

        # Step 3: Resume from Gate Node with tier choices
        selected_tiers = {mat["category"]: "Mid-Range" for mat in state.detected_materials}
        state = graph.resume_with_selections(state, selected_tiers)
        
        self.assertEqual(state.status, "COMPLETED")
        self.assertGreater(state.total_budget, 0.0)
        self.assertGreater(len(state.routed_builders), 0)

    def test_graph_flow_interior(self):
        state = AgentState(
            project_id="test-proj-int",
            scope="Interior",
            area=3000.0,
            image_path=self.dummy_image
        )
        graph = ArchitecturalSpecParserGraph()
        state = graph.run_next(state)
        
        self.assertEqual(state.status, "PAUSED")
        self.assertEqual(len(state.detected_materials), 10, "Interior should detect 10 categories")
        
        # Resume with Standard choices
        selected_tiers = {mat["category"]: "Standard" for mat in state.detected_materials}
        state = graph.resume_with_selections(state, selected_tiers)
        
        self.assertEqual(state.status, "COMPLETED")
        self.assertGreater(state.total_budget, 0.0)
        self.assertGreater(len(state.routed_builders), 0)

if __name__ == "__main__":
    unittest.main()
