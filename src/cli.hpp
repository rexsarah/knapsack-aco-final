#pragma once
#include <string>
#include <unordered_map>
#include <iostream>

struct Cli {
    std::string input_dir;   // default: "data/jooken"
    std::string output_dir;  // default: "results/jooken"
    std::string algo;        // opcional: AS|ASRank|MMAS|ACS
    bool help = false;
};

inline void print_usage(const char* argv0) {
    std::cout <<
R"(Usage:
  )" << argv0 << R"( [--input-dir PATH] [--output-dir PATH] [--algo NAME]

Options:
  --input-dir PATH     Pasta das instâncias (padrão: data/jooken)
  --output-dir PATH    Pasta dos resultados (padrão: results/jooken)
  --algo NAME          Variante (ex.: AS, ASRank, MMAS, ACS)
  -h, --help           Mostra esta ajuda
)";
}

inline Cli parse_cli(int argc, char** argv) {
    Cli cli;
    std::unordered_map<std::string, std::string*> map = {
        {"--input-dir",  &cli.input_dir},
        {"--output-dir", &cli.output_dir},
        {"--algo",       &cli.algo},
    };

    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        if (a == "-h" || a == "--help") { cli.help = true; continue; }
        auto it = map.find(a);
        if (it != map.end()) {
            if (i + 1 >= argc) { std::cerr << "Faltando valor para " << a << "\n"; cli.help = true; break; }
            *(it->second) = argv[++i];
        } else {
            // ignorar args desconhecidos para manter compatibilidade
        }
    }
    return cli;
}
