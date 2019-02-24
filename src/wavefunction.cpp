#include <random>
#include "definitions.hpp"
#include "wavefunction.hpp"
#include "sampler.hpp"
#include "mpiutil.hpp"

Wavefunction::Wavefunction(const RowVector& parameters)
    : _parameters(parameters) {}


RowVector Wavefunction::drift_force(const System& system) {
    const int n_particles = system.rows();
    const int n_dimensions = system.cols();
    RowVector force(system.size());

    for (int k = 0; k < n_particles; ++k)
        for (int d = 0; d < n_dimensions; ++d)
            force(n_dimensions * k + d) = drift_force(system, k, d);

    return force;
}

namespace {

/* Return n!, or cap if n! > cap.  */
unsigned capped_factorial(unsigned n, unsigned cap) {
    unsigned long fac = 1;
    for (unsigned i = 2; i <= n && fac < cap; fac *= i++);
    return std::min((unsigned) fac, cap);
}

void random_permutation(System& s) {
    assert(s.rows() > 1);
    std::uniform_int_distribution<int> uni(0, s.rows() - 1);
    int i = uni(rand_gen);
    int j = uni(rand_gen);
    while (i == j)
        j = uni(rand_gen);

    s.row(i).swap(s.row(j));
}

}


Real Wavefunction::symmetry_metric(Sampler& sampler, long samples, int max_permutations) {
    const System& s = sampler.get_current_system();

    if (s.rows() < 2)
        return 1;   // Single argument psi is symmetric by definition.

    // How many permutations? Ensure an even number.
    unsigned permutations = capped_factorial(s.rows(), max_permutations) & (~1U);

    Real num = 0;
    Real den = 0;
    for (long iter = 0; iter < samples; ++iter) {
        System s = sampler.next_configuration();
        Real base, sum;
        base = sum = (*this)(s);
        for (unsigned perm = 0; perm < permutations - 1; ++perm) {
            random_permutation(s);
            sum += (*this)(s);
        }
        sum /= permutations;
        num += sum * sum;
        den += base * base;
    }

    return num / den;
}
