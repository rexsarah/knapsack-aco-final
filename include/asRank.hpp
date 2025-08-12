#pragma once
#include <vector>
#include "problem.hpp"

class ASRank {
public:
    ASRank(int n, int iter, double a, double b, double r, int w, unsigned int seed);
    std::vector<int> executar(const KnapsackProblem& problema);

private:
    int numFormigas;
    int numIteracoes;
    double alfa, beta, rho;
    int w; // numero de ranks
    unsigned int seed_;
};
