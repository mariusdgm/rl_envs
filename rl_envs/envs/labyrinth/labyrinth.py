import gymnasium as gym
import numpy as np
import random
import pygame

from .maze import MazeFactory
from .constants import WALL, PATH, TARGET, START, PLAYER, COLORS, CELL_SIZE, Action
from .display import Display
from .player import Player


class Labyrinth(gym.Env):
    def __init__(
        self,
        rows,
        cols,
        maze_nr_desired_rooms=None,
        maze_nr_desired_rooms_range=(1, 8),
        maze_global_room_ratio=None,
        maze_global_room_ratio_range=(0.1, 0.8),
        room_access_points=None,
        room_access_points_range=(1, 4),
        room_types=None,
        room_ratio=None,
        room_ratio_range=(0.5, 1.5),
        reward_schema=None,
        seed=None,

    ):
        """
        Labyrinth environment for reinforcement learning.

        Arguments maze_num_rooms, maze_global_room_ratio, room_access_points 
        are used to fix specific values, otherwise the values are drawn from the minimum and maximum distibutions.
        
        room_types is used to determine what types of rooms are to be added in the maze, if None, the random seletion
        considers all the implemented room types

        Args:
           

        """
        
        super().__init__()

        self.rows, self.cols = rows, cols
        self.state = np.ones((rows, cols), dtype=np.uint8) * WALL

        if seed is None:
            seed = random.randint(0, 1e6)
        self.seed = seed  # this will change during every reset

        self.py_random = random.Random(seed)
        self.np_random = np.random.RandomState(seed)

        # Define action and observation spaces
        self.action_space = gym.spaces.Discrete(4)  # Up, Right, Down, Left
        self.observation_space = gym.spaces.Box(
            low=0, high=4, shape=(rows, cols), dtype=np.uint8
        )

        if not reward_schema:
            self.reward_schema = {
                "neutral_reward": -0.01,
                "wall_collision_reward": -1,
                "target_reached_reward": 10,
            }

        # Make Maze Factory
        self.maze_factory = MazeFactory(rows=self.rows,
                                        cols=self.cols,
                                        nr_desired_rooms=maze_nr_desired_rooms,
                                        nr_desired_rooms_range=maze_nr_desired_rooms_range,
                                        global_room_ratio=maze_global_room_ratio,
                                        global_room_ratio_range=maze_global_room_ratio_range,
                                        access_points_per_room=room_access_points,
                                        access_points_per_room_range=room_access_points_range,
                                        room_types=room_types,
                                        room_ratio=room_ratio,
                                        room_ratio_range=room_ratio_range,
                                        seed=self.seed)
        self.player = Player()

        self.setup_labyrinth()

        self.env_displayer = Display(self.rows, self.cols)

    def setup_labyrinth(self):
        maze_seed = self.np_random.randint(0, 1e6)
        self.maze = self.maze_factory.create_maze()
        self.player.position = self.maze.start_position
        self.build_state_matrix()
        
    def build_state_matrix(self):
        """Sequentially build the state matrix."""
        self.state = self.maze.grid.copy()
        self.state[self.maze.start_position] = START
        self.state[self.maze.target_position] = TARGET
        self.state[self.player.position] = PLAYER
        return self.state
    
    def step(self, action):
        # Initial reward
        reward = self.reward_schema["neutral_reward"]
        done = False
        truncated = False

        # Check if the action is valid
        if not self.is_valid_move(self.player, action):
            reward = self.reward_schema["wall_collision_reward"]
            return self.state, reward, done, truncated, {"info": "Invalid move!"}

        # Move the agent
        self.agent_move(action)

        # Check if the agent reached the target
        if self.player.position == self.maze.target_position:
            reward = self.reward_schema["target_reached_reward"]
            done = True
            return self.state, reward, done, truncated, {"info": "Reached the target!"}

        # Flush all info to state matrix
        self.state = self.build_state_matrix()

        return self.state, reward, done, truncated, {}
    
    def is_valid_move(self, player, action):
        potential_position = player.potential_next_position(action)
        is_inside_bounds = (0 <= potential_position[0] < self.rows) and \
                           (0 <= potential_position[1] < self.cols)
        if not is_inside_bounds:
            return False
        if self.maze.grid[potential_position[0], potential_position[1]] == WALL:
            return False
        return True
    
    def agent_move(self, action):
        new_position = self.player.potential_next_position(action)
        self.player.position = new_position

    def reset(self, seed=None):
        """Reset end and return a differenly seeded result

        Args:
            seed (int, optional): External seed if a user wants to provide one. Defaults to None.

        """
        # Increment the seed value
        if self.seed is None:
            self.seed = self.py_random.randint(0, 1e6)
        else:
            self.seed += 1

        self.setup_labyrinth()

    def seed(self, seed=None):
        self.seed = seed
        
    def render(self, mode=None, sleep_time=100):
        reward, done, info = None, None, None
        key_press = False

        self.env_displayer.draw_state(self.state)

        if mode == "human":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

                if event.type == pygame.KEYDOWN:
                    key_press = True

                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        quit()

                    if event.key == pygame.K_UP:
                        _, reward, done, _, info = self.step(Action.UP)
                    elif event.key == pygame.K_RIGHT:
                        _, reward, done, _, info = self.step(Action.RIGHT)
                    elif event.key == pygame.K_DOWN:
                        _, reward, done, _, info = self.step(Action.DOWN)
                    elif event.key == pygame.K_LEFT:
                        _, reward, done, _, info = self.step(Action.LEFT)

                        
        else:  # mode is not human, so model will play
            # Sleep for a bit so you can see the change
            pygame.time.wait(sleep_time)
            
        return self.state, reward, done, {}, info, key_press
    
    def human_play(self, print_info=False):
        """Continously display environment and allow user to play.
        Exit by closing the window or pressing ESC.
        """
        done = False
        while not done:  # Play one episode
            state, reward, done, _, info, key_pressed = env.render(mode="human")

            if print_info and key_pressed:
                print(f"Reward: {reward}, Done: {done}, Info: {info}")

            if done:
                env.reset()
        
if __name__ == "__main__":
    env = Labyrinth(31, 31)
    print_info = True

    done = False
    while True:  # Play one episode
        state, reward, done, _, info, key_pressed = env.render(mode="human")

        if print_info and key_pressed:
            print(f"Reward: {reward}, Done: {done}, Info: {info}")

        if done:
            env.reset()
