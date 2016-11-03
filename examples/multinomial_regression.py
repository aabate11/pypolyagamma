import numpy as np
import numpy.random as npr
npr.seed(1)
import matplotlib.pyplot as plt

import seaborn as sns
color_names = ["windows blue",
               "red",
               "amber",
               "faded green",
               "dusty purple",
               "crimson",
               "greyish"]
colors = sns.xkcd_palette(color_names)
sns.set_style("white")
from hips.plotting.colormaps import gradient_cmap

# from pgmult.utils import compute_psi_cmoments
from pybasicbayes.util.text import progprint_xrange
from pypolyagamma import MultinomialRegression
from pypolyagamma.utils import compute_psi_cmoments

def _plot_mult_probs(reg,
                     xlim=(-4,4), ylim=(-3,3), n_pts=100,
                     ax=None):
    XX,YY = np.meshgrid(np.linspace(*xlim,n_pts),
                        np.linspace(*ylim,n_pts))
    XY = np.column_stack((np.ravel(XX), np.ravel(YY)))

    D_reg = reg.D_in
    inputs = np.hstack((np.zeros((n_pts**2, D_reg-2)), XY))
    test_prs = reg.pi(inputs)

    if ax is None:
        fig = plt.figure(figsize=(10,6))
        ax = fig.add_subplot(111)

    for k in range(reg.K):
        start = np.array([1., 1., 1., 0.])
        end = np.concatenate((colors[k], [0.5]))
        cmap = gradient_cmap([start, end])
        im = ax.imshow(test_prs[:,k].reshape(*XX.shape),
                       extent=xlim + tuple(reversed(ylim)),
                       vmin=0, vmax=1, cmap=cmap)

        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

    plt.tight_layout()
    return ax

def test_multinomial_regression_2d(N=1000, N_iter=1000):
    ##########################################################
    # Construct multinomial regression to divvy up the space #
    ##########################################################
    K, D_in = 4, 2
    w1, b1 = np.array([+1.0, 0.0]), np.array([-2.0])  # x + b > 0 -> x > -b
    w2, b2 = np.array([-1.0, 0.0]), np.array([-2.0])  # -x + b > 0 -> x < b
    w3, b3 = np.array([0.0, +1.0]), np.array([0.0])  # y > 0

    reg_W = np.row_stack([w1, w2, w3][:K-1])
    reg_b = np.row_stack([b1, b2, b3][:K-1])

    # Scale the weights to make the transition boundary sharper
    reg_scale = 100.
    reg_b *= reg_scale
    reg_W *= reg_scale

    # Account for stick breaking asymmetry
    mu_b, _ = compute_psi_cmoments(np.ones(K))
    reg_b += mu_b[:, None]
    true_reg = MultinomialRegression(1, K, D_in, A=reg_W, b=reg_b)

    # Sample data from the model
    mask = np.ones((N, K-1), dtype=bool)
    X = np.random.randn(N,2).dot(np.diag([2,1]))
    y_oh = true_reg.rvs(x=X).astype(np.float)
    y = np.argmax(y_oh, axis=1)

    # Apply a random permutation
    perm = np.random.permutation(K)
    # perm = np.arange(K)
    y_oh_perm = y_oh[:, perm]
    y_perm = np.argmax(y_oh_perm, axis=1)

    # Create a test model for fitting
    test_reg = MultinomialRegression(1, K, D_in, sigmasq_A=10000., sigmasq_b=10000.)
    for itr in progprint_xrange(N_iter):
        test_reg.resample(datas=[(X, y_oh_perm[:,:-1])], masks=[mask])

    np.set_printoptions(precision=3)
    print("True A:\n{}".format(true_reg.A))
    print("True b:\n{}".format(true_reg.b))
    print("Test A:\n{}".format(test_reg.A))
    print("Test b:\n{}".format(test_reg.b))

    # Plot
    fig = plt.figure(figsize=(10,5))
    ax1 = fig.add_subplot(121)
    _plot_mult_probs(true_reg, ax=ax1)
    for k in range(K):
        ax1.plot(X[y==k, 0], X[y==k, 1], 'o', color=colors[k])
    ax1.set_title("True Probabilities and Data")

    ax2 = fig.add_subplot(122)
    _plot_mult_probs(test_reg, ax=ax2)
    for k in range(K):
        ax2.plot(X[y_perm == k, 0], X[y_perm == k, 1], 'o', color=colors[k])
    ax2.set_title("Inferred Probabilities for Permuted Data")
    plt.show()



if __name__ == "__main__":
    test_multinomial_regression_2d()