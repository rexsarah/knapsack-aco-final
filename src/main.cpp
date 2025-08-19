#include <iostream>
#include <vector>
#include <string>
#include <tuple>
#include <filesystem>
#include <cstdio>
#include <chrono>
#include <cmath>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <unordered_map>
#include <iomanip>
#include <cctype>

#include "../include/problem.hpp"
#include "../include/as.hpp"
#include "../include/asRank.hpp"
#include "../include/mmas.hpp"
#include "../include/acs.hpp"

namespace fs = std::filesystem;

// --------------------- helpers ---------------------

static std::vector<std::string> read_list(const std::string& path) {
    std::vector<std::string> files;
    std::ifstream in(path);
    if (!in) {
        std::cerr << "Could not open list file: " << path << "\n";
        return files;
    }
    std::string line;
    while (std::getline(in, line)) {
        size_t A = line.find_first_not_of(" \t\r\n");
        size_t B = line.find_last_not_of(" \t\r\n");
        if (A == std::string::npos) continue;
        line = line.substr(A, B - A + 1);
        if (line.empty() || line[0] == '#') continue;
        if (!fs::exists(line)) {
            std::cerr << "Warning: file from list does not exist: " << line << "\n";
            continue;
        }
        files.push_back(line);
    }
    return files;
}

static std::unordered_map<std::string,long long> loadTargets(const std::string& path) {
    // CSV: instance,optimal_value
    std::unordered_map<std::string,long long> tgt;
    std::ifstream in(path);
    if (!in) return tgt;

    auto trim = [](std::string s){
        size_t A = s.find_first_not_of(" \t\r\n");
        size_t B = s.find_last_not_of(" \t\r\n");
        if (A == std::string::npos) return std::string();
        return s.substr(A, B - A + 1);
    };
    auto is_int = [](const std::string& s){
        if (s.empty()) return false;
        size_t i = (s[0] == '+' || s[0] == '-') ? 1u : 0u;
        if (i >= s.size()) return false;
        for (; i < s.size(); ++i) {
            if (!std::isdigit(static_cast<unsigned char>(s[i]))) return false;
        }
        return true;
    };

    std::string line;
    while (std::getline(in, line)) {
        line = trim(line);
        if (line.empty() || line[0] == '#') continue;
        std::string a, b;
        std::istringstream ss(line);
        if (!std::getline(ss, a, ',')) continue;
        if (!std::getline(ss, b, ',')) continue;
        a = trim(a); b = trim(b);
        if (!is_int(b)) continue; // skip header
        try { tgt[a] = std::stoll(b); } catch (...) { /* ignore */ }
    }
    return tgt;
}

struct RunRec {
    long long value=0, weight=0;
    bool feasible=false;
    double seconds=0.0;
    unsigned int seed=0;
    std::vector<int> sel; // 1 if chosen (0-based positions), printing as 1-based ids
};

static std::tuple<long long,long long,bool>
evalSel(const std::vector<int>& sel, const KnapsackProblem& prob){
    long long V=0,W=0;
    const auto& itens = prob.getItens();
    for (size_t i=0;i<sel.size() && i<itens.size();++i) if (sel[i]) {
        V += itens[i].valor; W += itens[i].peso;
    }
    return {V,W, W<=prob.getCapacidade()};
}

static double mean(const std::vector<double>& v){
    if (v.empty()) return 0.0; double s=0.0; for(double x:v) s+=x; return s/v.size();
}
static double stdev(const std::vector<double>& v){
    if (v.size()<2) return 0.0; double m=mean(v), s2=0.0; for(double x:v) s2+=(x-m)*(x-m); return std::sqrt(s2/(v.size()-1));
}

static std::string itensToString(const std::vector<int>& sel){
    std::ostringstream oss; bool first=true;
    for (size_t i=0;i<sel.size();++i) if (sel[i]) { if(!first) oss<<" "; first=false; oss<<(i+1); }
    if (first) return "-"; return oss.str();
}

static void openCSVs(std::ofstream& csvExec, std::ofstream& csvSum){
    fs::create_directories("results/jooken");
    csvExec.open("results/jooken/execucoes_jooken.csv");
    csvSum.open("results/jooken/resumo_jooken.csv");
    // keep this header order
    csvExec << "instance,variant,run,seed,value,weight,feasible,seconds,items\n";
    csvSum  << "instance,variant,best_value,best_weight,feasible,best_seconds,mean_seconds,std_seconds,hit_optimal,target,best_seed\n";
}

// agora recebemos o rotulo da instancia (instLabel) ja normalizado
static void printResumo(const std::string& instLabel,
                        const std::string& var,
                        const KnapsackProblem& prob,
                        const std::vector<RunRec>& runs,
                        long long target,
                        std::ofstream& csvSum) {
    std::vector<double> times;
    times.reserve(runs.size());

    // escolhe melhor entre factiveis; se nenhum for factivel, pega o melhor valor mesmo assim
    long long bestV = -1;
    int bestIdx = -1;

    // primeiro, tenta apenas factiveis
    for (size_t i=0;i<runs.size();++i){
        times.push_back(runs[i].seconds);
        if (!runs[i].feasible) continue;
        if (runs[i].value > bestV) { bestV = runs[i].value; bestIdx=(int)i; }
    }
    // se nenhum factivel, considere todos
    if (bestIdx < 0) {
        for (size_t i=0;i<runs.size();++i){
            if (runs[i].value > bestV) { bestV = runs[i].value; bestIdx=(int)i; }
        }
    }

    const RunRec& best = runs[bestIdx];
    bool hit = (target >= 0 && best.value >= target && best.feasible);

    csvSum << instLabel << "," << var << ","
           << best.value << "," << best.weight << ","
           << (best.feasible?1:0) << "," << best.seconds << ","
           << mean(times) << "," << stdev(times) << ","
           << (hit?1:0) << "," << (target>=0?target:0) << ","
           << best.seed << "\n";
}

static void runVariant(const std::string& instLabel,
                       const std::string& var,
                       const KnapsackProblem& prob,
                       int repeats, unsigned int base_seed,
                       std::vector<RunRec>& out, std::ofstream& csvExec) {
    out.clear(); out.reserve(repeats);

    int ants=100, iters=600, w=5;
    double alpha=1.0, beta=3.0, rho=0.1, q0=0.90, xi=0.10;

    for (int rep=1; rep<=repeats; ++rep) {
        unsigned int seed = base_seed + (unsigned int)rep;
        std::vector<int> sel;
        auto t0 = std::chrono::high_resolution_clock::now();

        if (var=="AS") {
            AntSystem alg(ants, iters, alpha, beta, rho, seed);
            sel = alg.executar(prob);
        } else if (var=="ASRank") {
            ASRank alg(ants, iters, alpha, beta, rho, w, seed);
            sel = alg.executar(prob);
        } else if (var=="MMAS") {
            MMAS alg(ants, iters, alpha, beta, rho, seed);
            sel = alg.executar(prob);
        } else if (var=="ACS") {
            ACS alg(ants, iters, alpha, beta, rho, q0, xi, seed);
            sel = alg.executar(prob);
        } else {
            throw std::runtime_error("Unknown variant: " + var);
        }

        auto t1 = std::chrono::high_resolution_clock::now();
        std::chrono::duration<double> dt = t1 - t0;

        auto [V,W,ok] = evalSel(sel, prob);

        RunRec r; r.value=V; r.weight=W; r.feasible=ok; r.seconds=dt.count(); r.seed=seed; r.sel=std::move(sel);
        out.push_back(std::move(r));

        csvExec << instLabel << "," << var << "," << rep << ","
                << seed << "," << V << "," << W << "," << (ok?1:0) << ","
                << dt.count() << "," << itensToString(out.back().sel) << "\n";
    }
}

// --------------------- main ---------------------

int main(int argc, char** argv) {
    try {
        std::vector<std::string> files;

        if (argc == 3 && std::string(argv[1]) == "--list") {
            files = read_list(argv[2]);
        } else if (argc == 3 && std::string(argv[1]) == "--file") {
            if (!fs::exists(argv[2])) {
                std::cerr << "Input file not found: " << argv[2] << "\n";
                return 1;
            }
            files.push_back(argv[2]);
        } else {
            const std::string default_list = "config/sets/jooken_all.txt";
            files = read_list(default_list);
            if (files.empty()) {
                std::cerr << "No files found. Provide --list <file> or run the normalize script to generate "
                             "config/sets/jooken_all.txt\n";
                return 1;
            }
        }

        auto targets = loadTargets("config/targets.csv");

        std::ofstream csvExec, csvSum;
        openCSVs(csvExec, csvSum);

        const int repeats = 20;
        const unsigned int base_seed = 12345;

        for (const auto& path : files) {
            // rotulo da instancia: sempre usar o caminho lido da lista, normalizado
            std::string instLabel;
            try {
                instLabel = fs::weakly_canonical(path).string();
            } catch (...) {
                instLabel = fs::path(path).lexically_normal().string();
            }

            KnapsackProblem problem(path);

            long long alvo = -1;
            // tenta bater pelo caminho normalizado e pelo path original
            auto itA = targets.find(instLabel);
            if (itA != targets.end()) alvo = itA->second;
            if (alvo < 0) {
                auto itB = targets.find(path);
                if (itB != targets.end()) alvo = itB->second;
            }

            { std::vector<RunRec> runs; runVariant(instLabel, "AS", problem, repeats, base_seed, runs, csvExec);
              printResumo(instLabel, "AS", problem, runs, alvo, csvSum); }

            { std::vector<RunRec> runs; runVariant(instLabel, "ASRank", problem, repeats, base_seed+100000, runs, csvExec);
              printResumo(instLabel, "ASRank", problem, runs, alvo, csvSum); }

            { std::vector<RunRec> runs; runVariant(instLabel, "MMAS", problem, repeats, base_seed+200000, runs, csvExec);
              printResumo(instLabel, "MMAS", problem, runs, alvo, csvSum); }

            { std::vector<RunRec> runs; runVariant(instLabel, "ACS", problem, repeats, base_seed+300000, runs, csvExec);
              printResumo(instLabel, "ACS", problem, runs, alvo, csvSum); }
        }

        std::cout << "Done.\nResults saved to:\n"
                  << " - results/jooken/execucoes_jooken.csv\n"
                  << " - results/jooken/resumo_jooken.csv\n";
        return 0;

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }
}
