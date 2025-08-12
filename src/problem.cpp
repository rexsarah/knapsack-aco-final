#include "../include/problem.hpp"
#include <fstream>
#include <sstream>
#include <regex>
#include <algorithm>

static std::string basename_from_path(const std::string& p) {
    size_t pos = p.find_last_of("/\\");
    if (pos == std::string::npos) return p;
    return p.substr(pos + 1);
}
static std::string stem_from_path(const std::string& p) {
    std::string base = basename_from_path(p);
    size_t dot = base.find_last_of('.');
    return (dot == std::string::npos) ? base : base.substr(0, dot);
}

void KnapsackProblem::carregar(const std::string& filepath) {
    std::ifstream in(filepath);
    if (!in) throw std::runtime_error("Não foi possível abrir arquivo: " + filepath);

    std::stringstream buf; buf << in.rdbuf();
    std::string text = buf.str();

    // Extrai todos os inteiros (robusto a labels como "Capacidade", etc.)
    std::vector<long long> nums;
    std::regex re("-?\\d+");
    for (std::sregex_iterator it(text.begin(), text.end(), re), end; it != end; ++it) {
        nums.push_back(std::stoll((*it).str()));
    }
    if (nums.size() < 2) {
        throw std::runtime_error("Arquivo inválido (esperava pelo menos 2 números): " + filepath);
    }

    nome = stem_from_path(filepath);
    capacidade = static_cast<int>(nums[0]);
    int n = static_cast<int>(nums[1]);

    if (nums.size() < static_cast<size_t>(2 + 2 * n)) {
        std::ostringstream oss;
        oss << "Arquivo incompleto: esperava " << (2 + 2 * n)
            << " inteiros, obtive " << nums.size()
            << " em " << filepath;
        throw std::runtime_error(oss.str());
    }

    itens.clear();
    itens.reserve(n);
    size_t k = 2;
    for (int i = 0; i < n; ++i) {
        int v = static_cast<int>(nums[k++]);
        int w = static_cast<int>(nums[k++]);
        itens.push_back({ v, w });
    }
}

int KnapsackProblem::calcularValor(const std::vector<int>& selecao) const {
    int soma = 0;
    for (size_t i = 0; i < selecao.size() && i < itens.size(); ++i) {
        if (selecao[i]) soma += itens[i].valor;
    }
    return soma;
}
