
def update_theta(theta: float, correct: bool, lr: float = 0.25):
    return theta + lr if correct else theta - lr
