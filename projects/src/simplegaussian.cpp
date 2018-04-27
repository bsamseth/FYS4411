#include <cmath>
#include <cassert>

#include "definitions.hpp"
#include "vector.hpp"
#include "system.hpp"
#include "simplegaussian.hpp"

namespace {
    Real exponent(const System &system, Real beta) {
        Real g = 0;
        if (system.get_dimensions() == 3) {
            for (const Vector &boson : system.get_particles()) {
                g += square(boson[0]) + square(boson[1]) + beta * square(boson[2]);
            }
        } else {
            for (const Vector &boson : system.get_particles()) {
                g += square(boson);
            }
        }
        return g;
    }
}

SimpleGaussian::SimpleGaussian(std::initializer_list<Real> parameters)
    : Wavefunction(parameters)
{
    // Set default parameters.
    const static Vector defaults = std::vector<Real>{{0.5, 1}};
    _parameters = defaults;

    // Copy any given parameters.
    int i = 0;
    for (auto it = parameters.begin(); it != parameters.end() and i < defaults.size(); ++it, ++i)
        _parameters[i] = *it;
}

Real SimpleGaussian::operator() (System &system) const {
    const auto alpha = _parameters[0];
    const auto beta  = _parameters[1];
    return std::exp( - alpha * exponent(system, beta) );
}

Real SimpleGaussian::derivative_alpha(const System &system) const {
    const auto beta  = _parameters[1];
    return - exponent(system, beta);
}

Vector SimpleGaussian::gradient(System &system) const {
    const auto beta = _parameters[1];
    Vector grad(1);
    grad[0] = -exponent(system, beta);
    return grad;
}

Real SimpleGaussian::laplacian(System &system) const {
    const auto alpha = _parameters[0];
    const auto beta  = _parameters[1];
    const Real one_body_beta_term = - (system.get_dimensions() == 3 ? 2 + beta : system.get_dimensions());

    Real E_L = 0;

    for (int k = 0; k < system.get_n_particles(); ++k) {

        Vector r_k = system[k];
        if (system.get_dimensions() == 3) {
            r_k[2] *= beta;
        }

        E_L += 2 * alpha * (2 * alpha * (r_k * r_k) + one_body_beta_term);
    }

    return E_L;
}
