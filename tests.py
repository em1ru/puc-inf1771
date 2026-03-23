import unittest
import map_parser
import astar
import character_planner

class TestAvatarAIAssignment(unittest.TestCase):
    def setUp(self):
        # Setup the basic mocked environments ensuring stability
        self.synthetic_grid = [
            ['1', '.', 'R'],
            ['M', '.', 'V'],
            ['A', '.', '2']
        ]
        self.terrain_costs = {'.': 1, 'R': 5, 'V': 10, 'A': 15, 'M': 200, '1': 1, '2': 1}
        self.checkpoints = {'1': (0, 0), '2': (2, 2)}
        
        # Real params mock base
        self.agility = {"Aang": 1.8, "Zukko": 1.6, "Toph": 1.6, "Appa": 0.9}
        self.difficulties = {"1": 10, "2": 20, "3": 30}
        self.max_uses = 2
        
    def test_map_parser_is_walkable_always_true(self):
        """Map parser garante que nenhum tile é muro invisível absoluto"""
        self.assertTrue(map_parser.is_walkable('M'))
        
    def test_astar_synthetic_board(self):
        """A* testa desvios corretos nas montanhas e lagos achando as planícies ideais."""
        path, cost, nodes, etime = astar.astar(self.synthetic_grid, (0,0), (2,2), self.terrain_costs)
        
        self.assertGreater(cost, 0, "Custo deve ser estritamente acumulativo e superior a 0")
        self.assertGreater(nodes, 0, "A* precisa explorar pelo menos 1 nó!")
        # Rota correta pelas planícies do meu mock grid
        self.assertEqual(path, [(0,0), (0,1), (1,1), (2,1), (2,2)])
        self.assertEqual(cost, 4) # 4 movimentos custando '.' q é 1 cada
        
    def test_character_planner_hard_limit_respect(self):
        """Os solvers lógicos não devem JAMAIS ultrapassar os máximos de estamina dos chars"""
        greedy_dict = character_planner.greedy_assignment(self.difficulties, self.agility, self.max_uses)
        
        call_count = {k: 0 for k in self.agility.keys()}
        for stage, roster in greedy_dict.items():
            for c in roster:
                call_count[c] += 1
                
        for char, usages in call_count.items():
            self.assertLessEqual(usages, self.max_uses)
            
    def test_character_planner_calculation_formula(self):
        """Fórmula = N(diff)/Sum(agil) perfeitamente validada."""
        dummy_distro = {"1": ["Aang"], "2": ["Toph", "Appa"]}
        
        time_res = character_planner.calculate_total_time(dummy_distro, self.difficulties, self.agility)
        
        # 10 / 1.8 = 5.5555...
        # 20 / (1.6 + 0.9 = 2.5) = 8.0
        # Total = 13.5555...
        self.assertAlmostEqual(time_res, 13.555555555555555)
        
    def test_routing_engine(self):
         """Engine global de concactenação de rotas do A* deve ignorar overlap nos nós entre check-ins."""
         full_p, total_c, total_n, total_t = astar.find_route(self.synthetic_grid, self.checkpoints, ["1", "2"], self.terrain_costs)
         self.assertTrue(len(full_p) > 2)
         self.assertGreater(total_t, 0.0)

if __name__ == '__main__':
    unittest.main()
