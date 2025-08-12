// acs.cpp (Ant Colony System com seed controlada)
#include "../include/acs.hpp"
#include <random>
#include <algorithm>
#include <numeric>
#include <cmath>

ACS::ACS(int n, int iter, double a, double b, double r, double q0_, double xi_, unsigned int seed)
    : numFormigas(n), numIteracoes(iter), alfa(a), beta(b), rho(r), q0(q0_), xi(xi_), seed_(seed) {}

std::vector<int> ACS::executar(const KnapsackProblem& problema) {
    const auto& itens = problema.getItens();
    int n = (int)itens.size();
    int capacidade = problema.getCapacidade();

    std::vector<double> feromonio(n, 1.0);
    std::vector<double> visibilidade(n);
    for (int i = 0; i < n; ++i)
        visibilidade[i] = (double)itens[i].valor / (double)itens[i].peso;

    const double tau0 = 1.0; // constante pequena (ACS original usa tau0 pequeno)

    std::mt19937 gen(seed_);
    std::uniform_real_distribution<> dis(0.0, 1.0);

    std::vector<int> melhorSolucao(n, 0);
    long long melhorValor = -1;

    for (int iter = 0; iter < numIteracoes; ++iter) {
        for (int k = 0; k < numFormigas; ++k) {
            std::vector<int> solucao(n, 0);
            int pesoAtual = 0;

            while (true) {
                std::vector<double> desir(n, 0.0);
                double soma = 0.0;

                for (int i = 0; i < n; ++i) {
                    if (!solucao[i] && (pesoAtual + itens[i].peso <= capacidade)) {
                        desir[i] = std::pow(feromonio[i], alfa) * std::pow(visibilidade[i], beta);
                        soma += desir[i];
                    }
                }
                if (soma == 0.0) break;

                int escolhido = -1;
                if (dis(gen) < q0) {
                    double melhor = -1.0; int idx = -1;
                    for (int i = 0; i < n; ++i) if (desir[i] > melhor) { melhor = desir[i]; idx = i; }
                    escolhido = idx; // exploracao gulosa
                } else {
                    double r = dis(gen) * soma, total = 0.0;
                    for (int i = 0; i < n; ++i) {
                        total += desir[i];
                        if (total >= r) { escolhido = i; break; }
                    }
                }
                if (escolhido == -1) break;

                solucao[escolhido] = 1;
                pesoAtual += itens[escolhido].peso;

                // atualizacao local (ACS)
                feromonio[escolhido] = (1.0 - xi) * feromonio[escolhido] + xi * tau0;
            }

            long long valorAtual = problema.calcularValor(solucao);
            if (valorAtual > melhorValor) { melhorValor = valorAtual; melhorSolucao = solucao; }
        }

        // atualizacao global apenas com a melhor solucao (ACS)
        for (int i = 0; i < n; ++i) {
            feromonio[i] = (1.0 - rho) * feromonio[i];
            if (melhorSolucao[i] == 1) feromonio[i] += rho * (double)melhorValor;
        }
    }
    return melhorSolucao;
}
