import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn
import os
import tempfile
import time

figsize = (8, 8)
axis_fontsize = 26
title_fontsize = 20

def run_MC(dims=1, n=1, n_mc=100, alpha=0.5, beta=1,
           omega_z=1, a=0, step=0.1, importance=True,
           n_bins=500, max_radius=5,
           analytic=True, filename=None):
    """
    Main interface method to the C++ backend.

    Returns an array of energy values generated by the given parameters,
    and a list of numbers printed by the backend program, such as acceptance
    rate, execution time etc.
    """
    options = ('{} '*12).format(int(analytic),
                                int(importance),
                                dims,
                                n,
                                n_mc,
                                alpha,
                                beta,
                                omega_z,
                                a,
                                step,
                                n_bins,
                                max_radius)
    if filename:
        filename = filename + '_'.join(options.split(' '))
    else:
        filename = tempfile.mktemp(prefix='run-', suffix='_'.join(options.split(' ')))

    command = '../build-release/main.x {} {}'.format(options, filename)

    with os.popen(command) as cmd:
        output = cmd.read()
        ar, t = [float(i) for i in output.strip().split(',')]


    E = np.fromfile(filename + '_energy.bin', count=n_mc, dtype=np.float64)
    density = np.fromfile(filename + '_density.bin', count=n_bins, dtype=np.int64)

    meta = {'energy_mean' : np.mean(E),
            'variance' : np.var(E),
            'acceptance-rate' : ar,
            'time' : t}

    return E, density, meta


def E_and_var_plot_for_alphas(alphas, steps=(0.1,), verbose=True, saveas=None, **kwargs):
    E   = np.empty((len(steps), len(alphas)))
    var = np.empty((len(steps), len(alphas)))

    for i, step in enumerate(steps):
        kwargs['step'] = step
        for j, alpha in enumerate(alphas):
            kwargs['alpha'] = alpha
            _, _, res = run_MC(**kwargs)
            E[i, j], var[i, j] = res['energy-mean'], res['variance']

    min_E, min_var = np.argmin(E, axis=1), np.argmin(var, axis=1)


    if verbose:
        print(min_E, min_var, np.min(E, axis=1), np.min(var, axis=1))

    # Plot
    fig, ax = plt.subplots(nrows=2, sharex=True, figsize=figsize)
    for i, step in enumerate(steps):
        ax[0].plot(alphas, E[i, :], label=r'step$={}$'.format(step))
        ax[0].plot([alphas[min_E[i]]], [E[i, min_E[i]]], 'ro')

        ax[1].plot(alphas, var[i, :])
        ax[1].plot([alphas[min_var[i]]], [var[i, min_var[i]]], 'ro')

    ax[0].set_ylabel(r'$\langle H\rangle$', fontsize=axis_fontsize)
    ax[0].set_title(r'Ground state energy as function of variational parameter $\alpha$', fontsize=22)

    ax[1].set_xlabel(r'$\alpha$', fontsize=axis_fontsize)
    ax[1].set_ylabel(r'$\sigma^2_{E_L}$', fontsize=axis_fontsize)
    ax[1].set_title(r'Variance as function of variational parameter $\alpha$', fontsize=title_fontsize)

    plt.tight_layout()

    if len(steps) > 1:
        ax[0].legend(loc='upper right', bbox_to_anchor=(0, 0, 0.95, 0.95), fontsize=title_fontsize)

    if saveas:
        plt.savefig(saveas)

    plt.show()

    return E, var

def proper_error_plot(alphas, saveas=None, **kwargs):
    E = np.empty((len(alphas), kwargs['n_mc']))
    for i, alpha in enumerate(alphas):
        kwargs['alpha'] = alpha
        E[i], _, meta = run_MC(**kwargs)
        print(kwargs, 'meta=', meta)

    errors = [blocking(e) for e in E]

    fig, ax = plt.subplots(figsize=figsize)
    ax.errorbar(alphas, np.mean(E, axis=1), yerr=errors)
    ax.set_ylabel(r'$\langle H\rangle$', fontsize=axis_fontsize)
    ax.set_xlabel(r'$\alpha$', fontsize=axis_fontsize)
    ax.set_title(r'Ground state energy as function of variational parameter $\alpha$', fontsize=title_fontsize)

    if saveas:
        plt.savefig(saveas)

    return E, errors

def density_plot(density, max_radius = 5, saveas=None):

    # Normalize
    r = np.linspace(0, max_radius, len(density))
    rho = density / np.trapz(density, x=r)

    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(r, rho)
    ax.set_xlabel(r'$r$ $[a_{ho}]$', fontsize=axis_fontsize)
    ax.set_ylabel(r'$\rho$ $[a_{ho}]$', fontsize=axis_fontsize)
    ax.set_title(r'One-body density', fontsize=title_fontsize)


def make_configuration_table(filename, verbose=True, dims=(1,2,3), ns=(1, 10, 100, 500),
                             analytics=(1, 0), steps=(0.1,), importance=False, **kwargs):

    kwargs['importance'] = importance

    output =  'Dims, Nparticles, Analytic, step, Energy, Variance, Acceptance, Time\n'

    if verbose:
        print(output, end='')

    fmt = '{0:d}, {1:3d}, {2:d}, {3:4.6e}, {4:4.6e}, {5:4.2f}, {6:7.2e}, {7:}'

    for d in dims:
        kwargs['dims'] = d
        for n in [1, 10, 100, 500]:
            kwargs['n'] = n
            for analytic in [0, 1]:
                kwargs['analytic'] = analytic
                for step in steps:
                    kwargs['step'] = step

                    _, _, meta = run_MC(**kwargs)
                    energy, var, ar, t = meta['energy-mean'], meta['variance'], meta['acceptance-rate'], meta['time']

                    line = fmt.format(d, n, analytic, step, energy, var, ar, t)

                    if verbose:
                        print(line)

                    output += line + '\n'

    with open(filename, 'w') as f:
        f.write(output)


def bootstrap(data, statistic, B):
    """
    Return an array of B Bootstrap samples of the given statistic.
    """
    n = len(data)
    theta = np.empty(B)
    for i in range(B):
        theta[i] = statistic(np.random.choice(data, n, replace=True))
    return theta

def blocking(x):
    """
    Return an improved estimate of the standard error
    of the mean of the given time series, accounting for
    covariant samples.

    Code by Marius Jonsson.
    Adapted by Bendik Samseth
    """
    # preliminaries
    n     = len(x)
    d     = int(math.log2(n))
    s     = np.zeros(d)
    gamma = np.zeros(d)
    mu    = np.mean(x)

    # estimate the auto-covariance and variances
    # for each blocking transformation
    for i in range(0, d):
        n = len(x)
        # estimate autocovariance of x
        gamma[i] = np.sum( (x[0:(n-1)] - mu)*(x[1:n] - mu) ) / n
        # estimate variance of x
        s[i] = np.var(x)
        # perform blocking transformation
        x = 0.5 * (x[0::2] + x[1::2])

    # generate the test observator M_k from the theorem
    M = (np.cumsum(((gamma / s)**2 * 2**np.arange(1, d + 1)[::-1])[::-1] ))[::-1]

    # we need a list of magic numbers
    q = np.array([6.634897, 9.210340, 11.344867,
                  13.276704, 15.086272, 16.811894,
                  18.475307, 20.090235, 21.665994,
                  23.209251, 24.724970, 26.216967,
                  27.688250, 29.141238, 30.577914,
                  31.999927, 33.408664, 34.805306,
                  36.190869, 37.566235, 38.932173,
                  40.289360, 41.638398, 42.979820,
                  44.314105, 45.641683, 46.962942,
                  48.278236, 49.587884, 50.892181])

    # use magic to determine when we should have stopped blocking
    for k in range(0, d):
        if M[k] < q[k]:
            break

    if k >= d-1:
        print("Blocking warning: Blocked until stopped. Use more data if var != 0.")

    se = math.sqrt(s[k] / 2**(d - k))
    return se

def time_series_plot(E, saveas=None):
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(E, label=r'$E_L(t)$')
    ax.plot([0, len(E)-1], [np.mean(E)]*2, '--', label=r'$\overline E_L(t)$')
    ax.set_xlabel('Time', fontsize=axis_fontsize)
    ax.set_ylabel(r'$E_L$', fontsize=axis_fontsize)
    plt.legend(loc='best', fontsize=title_fontsize)

    if saveas:
        plt.savefig(saveas)

    plt.show()

