import math
import random
import numpy as np             # Handle matrices
from collections import deque  # Ordered collection with ends


"""
This part was taken from Udacity :
<a href="https://github.com/udacity/deep-learning/blob/master/reinforcement/Q-learning-cart.ipynb" Cartpole DQN</a>
"""


class Memory():

    def __init__(self, max_size):
        self.buffer = deque(maxlen=max_size)

    def add(self, experience):
        self.buffer.append(experience)

    def sample(self, batch_size):
        buffer_size = len(self.buffer)
        index = np.random.choice(np.arange(buffer_size),
                                 size=batch_size,
                                 replace=False)

        return [self.buffer[i] for i in index]


"""
Unit of a DQN
"""


class DQNUnit:

    def __init__(self, activation, deriv, inputs=None, weights=None):
        self.activation = activation
        self.deriv = deriv
        self.inputs = inputs or []
        self.weights = weights or []
        self.value = None


def linear(x):
    return x


def linear_deriv(x):
    return 1


def sigmoid(x):
    print("x: " + str(x))
    return 1 / (1 + (math.e ** (-x)))


def sigmoid_deriv(x):
    sx = sigmoid(x)
    return sx * (1 - sx)


def elu(x, alpha=0.01):
    return x if x > 0 else alpha * (math.e ** x - 1)


def elu_deriv(x, alpha=0.01):
    return 1 if x > 0 else elu(x) + alpha


def relu(x):
    return x if x > 0 else 0


def relu_deriv(x):
    if x > 0:
        return 1
    if x < 0:
        return 0


class DQNetwork:

    """
    Our parameters:
        input_layer_size=24
        hidden_layer_size=[128,256]
        output_layer_size=22
    """

    def __init__(self, input_layer_size=24, hidden_layer_sizes=[128, 256], output_layer_size=22,
                 hidden_activation=relu, hidden_deriv=relu_deriv, output_activation=linear, output_deriv=linear_deriv):
        non_ouput_layer_sizes = [input_layer_size] + hidden_layer_sizes
        network = [[DQNUnit(hidden_activation, hidden_deriv) for _ in range(s)]
                   for s in non_ouput_layer_sizes]
        network += [[DQNUnit(output_activation, output_deriv) for _ in range(t)]
                    for t in [output_layer_size]]
        dummy_node = DQNUnit(hidden_activation, hidden_deriv)
        dummy_node.value = 1.0

        # initialize weighted links with random values from uniform distribution
        layer_sizes = non_ouput_layer_sizes + [output_layer_size]
        for layer_idx in range(1, len(layer_sizes)):
            for node in network[layer_idx]:
                node.inputs.append(dummy_node)
                node.weights.append(0.0)
                for input_node in network[layer_idx - 1]:
                    node.inputs.append(input_node)
                    node.weights.append(random.uniform(-0.5, 0.5))
        self.network = network

    def Q(self, sf):
        print("Q")
        print("Q Input: " + str(sf))
        new_sf = self.normalize(sf)
        print("Normalized Q Input: " + str(new_sf))
        inputs = []     # inputs: 2-D list for storing weighted input sums to units
        Q_vec = []
        for layer in self.network:
            inputs.append([0] * len(layer))
        # iu: input unit (index)
        for iu in range(len(self.network[0])):
            self.network[0][iu].value = new_sf[iu]
        # nil: non input layer (index)
        for nil in range(1, len(self.network)):
            # niu: non input unit (index)
            for niu in range(len(self.network[nil])):
                ni_unit = self.network[nil][niu]
                weighted_inputs = 0
                # itc: input to current (index)
                for itc in range(len(ni_unit.inputs)):
                    weighted_inputs += ni_unit.inputs[itc].value * \
                        ni_unit.weights[itc]
                ni_unit.value = ni_unit.activation(weighted_inputs)
                inputs[nil][niu] = weighted_inputs
        output_layer = len(self.network) - 1
        # ou: output unit (index)
        for ou in range(len(self.network[output_layer])):
            Q_vec.append(self.network[output_layer][ou].value)
            print("Q unit output: " +
                  str(self.network[output_layer][ou].value))

        return self.normalize(Q_vec)

    def normalize(self, vector):
        print("Normalizing")
        abs_sum = 0
        for i in vector:
            abs_sum += abs(i)
        output = []
        print("Absolute sum: " + str(abs_sum))
        for j in vector:
            output.append(j / abs_sum)
        return output

    """
    Returns a neural network trained using back propagation

    This function initializes the weights in the given network, [network], with random values from a uniform distribution
    and error vector delta with 0 for each unit. Then, for each example in [examples], it propagates the inputs through
    the network to compute the outputs, using the activation functions of the network units. The outputs are then
    compared to the desired outputs for the example and used to generate the deltas in the output layer which are then
    propagated backward to the input layer. Once deltas have been calculated for each unit, the values are used to
    update the weights. The alpha value is given by the [learning_rate] parameter. This process continues like this for
    all examples and then repeats according to the given number of epochs ([epochs]). Finally, the network is returned
    along with information on the total mean squared error per epoch as calculated above.

    Parameter examples: the list of examples to train with.
    Precondition: examples is a non-empty list of examples that fits the network so that the number of inputs
        and outputs in each example matches the number of input units and output units in the network and the input
        and output vectors in each example only contain appropriate values for the network.
    Parameter epochs: the number of epochs for the training process.
    Precondition: epochs is a positive (non-zero) integer.
    Paramter learning_rate: the learning rate to be used when updating weights.
    Precondition: learning_rate is a number.
    Parameter gamma: the decay rate
    Precondition: gamma is a float in the range (0,1)
    """

    def update_weights(self, exps, epochs=5, learning_rate=0.01, gamma=0.9):
        print("Training")
        delta = []      # delta: 2-D list for the delta error vector
        inputs = []     # inputs: 2-D list for storing weighted input sums to units
        for layer in self.network:
            delta.append([0] * len(layer))
            inputs.append([0] * len(layer))
        for i in range(epochs):
            print("Epoch: " + str(i))
            for j in range(len(exps)):
                print("Experience: " + str(j))
                state = exps[j][0]
                Q_vec = self.Q(state)
                reward = exps[j][2]
                print("Reward: " + str(reward))
                new_state = exps[j][3]
                winning = (state[24] - new_state[10] > 0)

                for non_input_layer in range(1, len(self.network)):
                    for non_input_unit_idx in range(len(self.network[non_input_layer])):
                        ni_unit = self.network[non_input_layer][non_input_unit_idx]
                        weighted_inputs = 0
                        for input_to_unit in range(len(ni_unit.inputs)):
                            weighted_inputs += ni_unit.inputs[input_to_unit].value * \
                                ni_unit.weights[input_to_unit]
                        ni_unit.value = ni_unit.activation(weighted_inputs)
                        inputs[non_input_layer][non_input_unit_idx] = weighted_inputs

                output_layer = len(self.network) - 1
                for output_unit_idx in range(len(self.network[output_layer])):
                    # Qmax is 0 if ai is losing, 1 if winning (for now)
                    Q_max = 1 if winning else 0
                    Q_est = Q_vec[output_unit_idx]
                    delta[output_layer][output_unit_idx] = learning_rate * \
                        ((reward + gamma * Q_max) - Q_est) * \
                        self.network[output_layer][output_unit_idx].deriv(
                        Q_est)

                # nol: non output layer (index)
                for nol in range(output_layer - 1, 0, -1):
                    # nou: non output unit (index)
                    for nou in range(len(self.network[nol])):
                        # forward_deltas: deltas of forward linked units
                        forward_deltas = []
                        # forward_weights: weights on forward links
                        forward_weights = []
                        # flu: forward linked unit (index)
                        for flu in range(len(self.network[nol + 1])):
                            fl_unit = self.network[nol + 1][flu]
                            # itf: input to forward (index)
                            for itf in range(len(fl_unit.inputs)):
                                if fl_unit.inputs[itf] == self.network[nol][nou]:
                                    forward_deltas.append(delta[nol + 1][flu])
                                    forward_weights.append(
                                        fl_unit.weights[itf])
                                    break
                        partial_delta = 0
                        # fd: forward delta (index)
                        for fd in range(len(forward_deltas)):
                            partial_delta += forward_deltas[fd] * \
                                forward_weights[fd]
                        delta[nol][nou] = self.network[nol][nou].activation(
                            inputs[nol][nou]) * partial_delta
                # l: layer in network
                for l in range(len(self.network)):
                    # u: unit in layer
                    for u in range(len(self.network[l])):
                        unit = self.network[l][u]
                        for w in range(len(unit.weights)):           # w: weight to unit
                            #print("Old weight: " + str(unit.weights[w]))
                            unit.weights[w] += learning_rate * \
                                unit.inputs[w].value * delta[l][u]
                            #print("New weight: " + str(unit.weights[w]))
        print("Training Complete")
