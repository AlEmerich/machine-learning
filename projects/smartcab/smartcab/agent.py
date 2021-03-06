import random
import math
import argparse
from environment import Agent, Environment
from planner import RoutePlanner
from simulator import Simulator

class LearningAgent(Agent):
    """ An agent that learns to drive in the Smartcab world.
        This is the object you will be modifying. """ 

    def __init__(self, env, learning=False, epsilon=1.0, alpha=0.5,
                 decay_fun=0, decay=0.5):
        super(LearningAgent, self).__init__(env)     # Set the agent in the evironment 
        self.planner = RoutePlanner(self.env, self)  # Create a route planner
        self.valid_actions = self.env.valid_actions  # The set of valid actions

        # Set parameters of the learning agent
        self.learning = learning # Whether the agent is expected to learn
        self.Q = dict()          # Create a Q-table which will be a dictionary of tuples
        self.epsilon = epsilon   # Random exploration factor
        self.alpha = alpha       # Learning factor
        self.t = 0
        self.decay_fun = decay_fun
        if decay_fun > 4:
            self.decay_fun = 0
        self.decay = decay

    def reset(self, destination=None, testing=False):
        """ The reset function is called at the beginning of each trial.
            'testing' is set to True if testing trials are being used
            once training trials have completed. """

        # Select the destination as the new location to route to
        self.planner.route_to(destination)
        self.t = self.t + 1

        # Update epsilon using a decay function of your choice
        # Update additional class parameters as needed
        # If 'testing' is True, set epsilon and alpha to 0
        if testing is True:
            self.epsilon = 0
            self.alpha = 0
        else:
            if self.decay_fun == 0:
                self.epsilon = self.epsilon - self.decay
            elif self.decay_fun == 1:
                self.epsilon = 1 / (self.t * self.t)
            elif self.decay_fun == 2:
                self.epsilon = self.epsilon * ((1 - self.decay) ** self.t)
            elif self.decay_fun == 3:
                self.epsilon = math.exp(-self.decay * self.t)
            elif self.decay_fun == 4:
                self.epsilon = math.cos(self.decay * self.t)
        return None

    def build_state(self):
        """ The build_state function is called when the agent requests data from the 
            environment. The next waypoint, the intersection inputs, and the deadline 
            are all features available to the agent. """

        # Collect data about the environment
        waypoint = self.planner.next_waypoint() # The next waypoint 
        inputs = self.env.sense(self)           # Visual input - intersection light and traffic
        deadline = self.env.get_deadline(self)  # Remaining deadline

        # NOTE : you are not allowed to engineer eatures outside of the inputs available.
        # Because the aim of this project is to teach Reinforcement Learning, we have placed
        # constraints in order for you to learn how to adjust epsilon and alpha, and thus learn about the balance between exploration and exploitation.
        # With the hand-engineered features, this learning process gets entirely negated.

        # Set 'state' as a tuple of relevant data for the agent
        state = (inputs['light'], waypoint, inputs['oncoming'], inputs['left'])
        return state


    def get_maxQ(self, state):
        """ The get_max_Q function is called when the agent is asked to find the
            maximum Q-value of all actions based on the 'state' the smartcab is in. """

        # Calculate the maximum Q-value of all actions for a given state
        maxQ = max(self.Q[state].values())
        return maxQ


    def createQ(self, state):
        """ The createQ function is called when a state is generated by the agent. """

        # When learning, check if the 'state' is not in the Q-table
        # If it is not, create a new dictionary for that state
        #   Then, for each action available, set the initial Q-value to 0.0
        if self.learning:
            if state not in self.Q:
                self.Q[state] = {
                    None: 0.,
                    'left': 0.,
                    'right': 0.,
                    'forward': 0.
                }
        return


    def choose_action(self, state):
        """ The choose_action function is called when the agent is asked to choose
            which action to take, based on the 'state' the smartcab is in. """

        # Set the agent state and default action
        self.state = state
        self.next_waypoint = self.planner.next_waypoint()
        action = None

        # When not learning, choose a random action
        # When learning, choose a random action with 'epsilon' probability
        # Otherwise, choose an action with the highest Q-value for the current state
        # Be sure that when choosing an action with highest Q-value that you randomly select between actions that "tie".
        if not self.learning:
            action = random.choice(self.valid_actions)
        else:
            max_value = self.get_maxQ(state)
            actions = [k for k, v in self.Q[state].items() if v == max_value]
            action = random.choice(actions)

            x = random.uniform(0, 1)
            if x < self.epsilon:
                action = random.choice(self.valid_actions)
        return action


    def learn(self, state, action, reward):
        """ The learn function is called after the agent completes an action and
            receives a reward. This function does not consider future rewards 
            when conducting learning. """

        # When learning, implement the value iteration update rule
        #   Use only the learning rate 'alpha' (do not use the discount factor 'gamma')
        # https://www.cs.rutgers.edu/~mlittman/courses/cps271/lect-16/node16.html
        if self.learning:
            Qvalue = self.Q[state][action]
            self.Q[state][action] = (1 - self.alpha)*Qvalue + self.alpha * reward
        return


    def update(self):
        """ The update function is called when a time step is completed in the 
            environment for a given trial. This function will build the agent
            state, choose an action, receive a reward, and learn if enabled. """

        state = self.build_state()          # Get current state
        self.createQ(state)                 # Create 'state' in Q-table
        action = self.choose_action(state)  # Choose an action
        reward = self.env.act(self, action) # Receive a reward
        self.learn(state, action, reward)   # Q-learn
        return


def run(args):
    """ Driving function for running the simulation. 
        Press ESC to close the simulation, or [SPACE] to pause the simulation. """

    raw_input(args)
    ##############
    # Create the environment
    # Flags:
    #   verbose     - set to True to display additional output from the simulation
    #   num_dummies - discrete number of dummy agents in the environment, default is 100
    #   grid_size   - discrete number of intersections (columns, rows), default is (8, 6)
    env = Environment(bool(args.verbose), int(args.num_dummies),
                      args.grid_size)

    ##############
    # Create the driving agent
    # Flags:
    #   learning   - set to True to force the driving agent to use Q-learning
    #    * epsilon - continuous value for the exploration factor, default is 1
    #    * alpha   - continuous value for the learning rate, default is 0.5
    agent = env.create_agent(LearningAgent, bool(args.learning),
                             float(args.epsilon), float(args.alpha),
                             int(args.decay_fun), float(args.decay))
    ##############
    # Follow the driving agent
    # Flags:
    #   enforce_deadline - set to True to enforce a deadline metric
    env.set_primary_agent(agent, bool(args.enforce_deadline))
    ##############
    # Create the simulation
    # Flags:
    #   update_delay - continuous time (in seconds) between actions, default is 2.0 seconds
    #   display      - set to False to disable the GUI if PyGame is enabled
    #   log_metrics  - set to True to log trial and simulation results to /logs
    #   optimized    - set to True to change the default log file name
    sim = Simulator(env, update_delay=float(args.update_delay), display=args.display,
                    log_metrics=bool(args.log_metrics), optimized=bool(args.optimized))

    ##############
    # Run the simulator
    # Flags:
    #   tolerance  - epsilon tolerance before beginning testing, default is 0.05
    #   n_test     - discrete number of testing trials to perform, default is 0
    sim.run(float(args.tolerance), int(args.n_test))

def toBool(arg):
    """Parse string argument to bool type."""
    if arg in ("yes", "y", "True", "true", "t", "1"):
        return True
    elif arg in ("no", "n", "False", "false", "f", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean Value expected")

if __name__ == '__main__':
    parser = argparse.ArgumentParser("Udacity - SmartCab simulation agent")
    parser.add_argument('--verbose', default=False, type=toBool)
    parser.add_argument('--num_dummies', default=100, type=float)
    parser.add_argument('--grid_size', default=(8, 6))

    parser.add_argument('--learning', default=False, type=toBool)
    parser.add_argument('--epsilon', default=1, type=float)
    parser.add_argument('--alpha', default=0.5, type=float)
    parser.add_argument('--decay_fun', default=0, type=int)
    parser.add_argument('--decay', default=0.5, type=float)

    parser.add_argument('--enforce_deadline', default=False, type=toBool)

    parser.add_argument('--update_delay', default=2.0, type=float)
    parser.add_argument('--display', default=True, type=toBool)
    parser.add_argument('--log_metrics', default=False, type=toBool)
    parser.add_argument('--optimized', default=False, type=toBool)
    parser.add_argument('--tolerance', default=0.05, type=float)
    parser.add_argument('--n_test', default=0, type=int)
    run(parser.parse_args())
