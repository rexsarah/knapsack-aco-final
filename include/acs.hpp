#pragma once
#include <vector>
#include "problem.hpp"

class ACS {
public:
    ACS(int n, int iter, double a, double b, double r, double q0_, double xi_, unsigned int seed);
    std::vector<int> executar(const KnapsackProblem& problema);

private:
    int numFormigas;
    int numIteracoes;
    double alfa, beta, rho, q0, xi;
    unsigned int seed_;
};
