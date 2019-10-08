import p3.Network as net

"""
write the weights in DQNetwork network to p3/weights.txt
"""
def write_file(network):
    weight_list = []
    for layer_idx in range(4):
        acc = []
        for unit in network.network[layer_idx]:
            weights = []
            for x in unit.weights:
                weights += [str(x)+"\n"]
            acc += weights
        weight_list += acc
    file = open("p3/weights.txt","w")
    file.writelines(weight_list)
    file.close()

"""
reads the weights in p3/weights.txt and returns a DQNetwork object
"""
def read_file():
    dqn = net.DQNetwork()
    file = open("p3/random_weights.txt","r")
    entire_list = file.readlines()
    for layer_idx in range(3):
        if layer_idx == 0:
            for hl_1_idx in range(128):
                for weight in range(25):
                    dqn.network[layer_idx+1][hl_1_idx].weights[weight] = float((entire_list[(hl_1_idx*25)+weight])[:-2])
        elif layer_idx == 1:
            for hl_2_idx in range(256):
                for weight in range(129):
                    dqn.network[layer_idx+1][hl_2_idx].weights[weight] = float((entire_list[3200+(hl_2_idx*129)+weight])[:-2])
        elif layer_idx == 2:
            for ol_idx in range(22):
                for weight in range(257):
                    dqn.network[layer_idx+1][ol_idx].weights[weight] = float((entire_list[36224+(ol_idx*257)+weight])[:-2])
    file.close()
    return dqn
