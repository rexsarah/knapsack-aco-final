// src/problem.cpp
#include "problem.hpp"
#include <fstream>
#include <sstream>

static std::string trim(const std::string& s) {
    auto a = s.find_first_not_of(" \t\r\n");
    if (a == std::string::npos) return "";
    auto b = s.find_last_not_of(" \t\r\n");
    return s.substr(a, b - a + 1);
}

static std::string stem_from_path(const std::string& p) {
    auto slash = p.find_last_of("/\\");
    std::string fn = (slash == std::string::npos) ? p : p.substr(slash + 1);
    auto dot = fn.find_last_of('.');
    return (dot == std::string::npos) ? fn : fn.substr(0, dot);
}

void KnapsackProblem::load(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("Nao foi possivel abrir: " + path);

    std::vector<long long> nums;
    nums.reserve(1024);
    std::string line;

    while (std::getline(in, line)) {
        line = trim(line);
        if (line.empty()) continue;

        std::stringstream ss(line);
        while (!ss.eof()) {
            std::string tok;
            ss >> tok;
            if (tok.empty()) break;

            // aceita 12.34, 12,34, 12e3 etc -> converte vírgula p/ ponto
            for (auto& c : tok) if (c == ',') c = '.';

            try {
                size_t idx = 0;
                double d = std::stod(tok, &idx);
                if (idx == tok.size()) {
                    long long v = static_cast<long long>(d);
                    nums.push_back(v);
                }
            } catch (...) {
                // ignora tokens não numéricos
            }
        }
    }

    if (nums.size() < 2) {
        throw std::runtime_error("Arquivo invalido (poucos numeros): " + path);
    }

    name_ = stem_from_path(path);
    capacity_ = static_cast<int>(nums[0]);
    int n = static_cast<int>(nums[1]);

    if (nums.size() < 2 + 2LL * n) {
        throw std::runtime_error("Arquivo invalido (esperava 2*n valores): " + path);
    }

    items_.clear();
    items_.reserve(n);
    size_t k = 2;
    for (int i = 0; i < n; ++i) {
        long long v = nums[k++];   // value
        long long w = nums[k++];   // weight
        Item it;
        it.value  = v;
        it.weight = w;
        items_.push_back(it);
    }
}
