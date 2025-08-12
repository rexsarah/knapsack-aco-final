// as.cpp (Ant System com feromonio compartilhado e seed controlada)
#include "../include/as.hpp"
#include <random>
#include <algorithm>
#include <numeric>
#include <cmath>

AntSystem::AntSystem(int n, int iter, double a, double b, double r, unsigned int seed)
    : numFormigas(n), numIteracoes(iter), alfa(a), beta(b), rho(r), seed_(seed) {}

std::vector<int> AntSystem::executar(const KnapsackProblem& problema) {
    const auto& itens = problema.getItens();
    int n = (int)itens.size();
    int capacidade = problema.getCapacidade();

    // Feromonio COMPARTILHADO (corrigido)
    std::vector<double> feromonio(n, 1.0);
    std::vector<double> visibilidade(n);
    for (int i = 0; i < n; ++i)
        visibilidade[i] = (double)itens[i].valor / (double)itens[i].peso;

    std::mt19937 gen(seed_);
    std::uniform_real_distribution<> dis(0.0, 1.0);

    std::vector<int> melhorSolucao(n, 0);
    long long melhorValor = -1;

    for (int iter = 0; iter < numIteracoes; ++iter) {
        std::vector<std::vector<int>> solucoes(numFormigas, std::vector<int>(n, 0));
        std::vector<long long> valores(numFormigas, 0);

        for (int k = 0; k < numFormigas; ++k) {
            int pesoAtual = 0;

            while (true) {
                std::vector<double> prob(n, 0.0);
                double somaProb = 0.0;

                for (int i = 0; i < n; ++i) {
                    if (solucoes[k][i] == 0 && pesoAtual + itens[i].peso <= capacidade) {
                        prob[i] = std::pow(feromonio[i], alfa) * std::pow(visibilidade[i], beta);
                        somaProb += prob[i];
                    }
                }

                if (somaProb == 0.0) break;

                double r = dis(gen) * somaProb;
                double total = 0.0;
                int escolhido = -1;
                for (int i = 0; i < n; ++i) {
                    total += prob[i];
                    if (total >= r) { escolhido = i; break; }
                }
                if (escolhido == -1) break;

                solucoes[k][escolhido] = 1;
                pesoAtual += itens[escolhido].peso;
            }

            // avalia
            long long v = problema.calcularValor(solucoes[k]);
            valores[k] = v;
            if (v > melhorValor) { melhorValor = v; melhorSolucao = solucoes[k]; }
        }

        // Atualizacao global do feromonio (compartilhado)
        for (int i = 0; i < n; ++i) {
            feromonio[i] = (1.0 - rho) * feromonio[i];
        }
        for (int k = 0; k < numFormigas; ++k) {
            for (int i = 0; i < n; ++i) {
                if (solucoes[k][i] == 1) {
                    // Em AS ant-cycle original: deposito ~ 1/Lk (minimizacao).
                    // Aqui usamos valor da mochila (maximizacao).
                    feromonio[i] += rho * (double)valores[k];
                }
            }
        }
    }
    return melhorSolucao;
}
