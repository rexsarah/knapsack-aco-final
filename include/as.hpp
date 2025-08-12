#pragma once
#include <vector>
#include "problem.hpp"

class AntSystem {
public:
    AntSystem(int n, int iter, double a, double b, double r, unsigned int seed);
    std::vector<int> executar(const KnapsackProblem& problema);

private:
    int numFormigas;
    int numIteracoes;
    double alfa, beta, rho;
    unsigned int seed_;
};
