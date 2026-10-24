export interface AeroportoInfo {
  iata: string;
  cidade: string;
  nome: string;
  uf: string;
  regiao: string;
}

export const LISTA_AEROPORTOS: AeroportoInfo[] = [
  // Sudeste
  { iata: 'GRU', cidade: 'São Paulo', nome: 'Guarulhos Internacional', uf: 'SP', regiao: 'Sudeste' },
  { iata: 'CGH', cidade: 'São Paulo', nome: 'Congonhas', uf: 'SP', regiao: 'Sudeste' },
  { iata: 'VCP', cidade: 'Campinas', nome: 'Viracopos Internacional', uf: 'SP', regiao: 'Sudeste' },
  { iata: 'RAO', cidade: 'Ribeirão Preto', nome: 'Leite Lopes', uf: 'SP', regiao: 'Sudeste' },
  { iata: 'SJP', cidade: 'São José do Rio Preto', nome: 'Eribelto Manoel Reino', uf: 'SP', regiao: 'Sudeste' },
  { iata: 'PPB', cidade: 'Presidente Prudente', nome: 'Adhemar de Barros', uf: 'SP', regiao: 'Sudeste' },
  { iata: 'BAU', cidade: 'Bauru', nome: 'Bauru-Arealva', uf: 'SP', regiao: 'Sudeste' },
  { iata: 'GIG', cidade: 'Rio de Janeiro', nome: 'Galeão Internacional', uf: 'RJ', regiao: 'Sudeste' },
  { iata: 'SDU', cidade: 'Rio de Janeiro', nome: 'Santos Dumont', uf: 'RJ', regiao: 'Sudeste' },
  { iata: 'CFB', cidade: 'Cabo Frio', nome: 'Cabo Frio Internacional', uf: 'RJ', regiao: 'Sudeste' },
  { iata: 'CNF', cidade: 'Belo Horizonte', nome: 'Confins Internacional', uf: 'MG', regiao: 'Sudeste' },
  { iata: 'UDI', cidade: 'Uberlândia', nome: 'César Bombonato', uf: 'MG', regiao: 'Sudeste' },
  { iata: 'MOC', cidade: 'Montes Claros', nome: 'Mário Ribeiro', uf: 'MG', regiao: 'Sudeste' },
  { iata: 'IZA', cidade: 'Juiz de Fora', nome: 'Zona da Mata', uf: 'MG', regiao: 'Sudeste' },
  { iata: 'VIX', cidade: 'Vitória', nome: 'Eurico de Aguiar Salles', uf: 'ES', regiao: 'Sudeste' },

  // Nordeste
  { iata: 'REC', cidade: 'Recife', nome: 'Guararapes Internacional', uf: 'PE', regiao: 'Nordeste' },
  { iata: 'FEN', cidade: 'Fernando de Noronha', nome: 'Gov. Carlos Wilson', uf: 'PE', regiao: 'Nordeste' },
  { iata: 'PNZ', cidade: 'Petrolina', nome: 'Sen. Nilo Coelho', uf: 'PE', regiao: 'Nordeste' },
  { iata: 'SSA', cidade: 'Salvador', nome: 'Dep. Luís Eduardo Magalhães', uf: 'BA', regiao: 'Nordeste' },
  { iata: 'BPS', cidade: 'Porto Seguro', nome: 'Porto Seguro', uf: 'BA', regiao: 'Nordeste' },
  { iata: 'IOS', cidade: 'Ilhéus', nome: 'Jorge Amado', uf: 'BA', regiao: 'Nordeste' },
  { iata: 'VDC', cidade: 'Vitória da Conquista', nome: 'Glauber Rocha', uf: 'BA', regiao: 'Nordeste' },
  { iata: 'FOR', cidade: 'Fortaleza', nome: 'Pinto Martins Internacional', uf: 'CE', regiao: 'Nordeste' },
  { iata: 'JJD', cidade: 'Jericoacoara', nome: 'Cruz / Jericoacoara', uf: 'CE', regiao: 'Nordeste' },
  { iata: 'JDO', cidade: 'Juazeiro do Norte', nome: 'Orlando Bezerra', uf: 'CE', regiao: 'Nordeste' },
  { iata: 'NAT', cidade: 'Natal', nome: 'São Gonçalo do Amarante', uf: 'RN', regiao: 'Nordeste' },
  { iata: 'MCZ', cidade: 'Maceió', nome: 'Zumbi dos Palmares', uf: 'AL', regiao: 'Nordeste' },
  { iata: 'JPA', cidade: 'João Pessoa', nome: 'Presidente Castro Pinto', uf: 'PB', regiao: 'Nordeste' },
  { iata: 'CPV', cidade: 'Campina Grande', nome: 'Presidente João Suassuna', uf: 'PB', regiao: 'Nordeste' },
  { iata: 'AJU', cidade: 'Aracaju', nome: 'Santa Maria', uf: 'SE', regiao: 'Nordeste' },
  { iata: 'SLZ', cidade: 'São Luís', nome: 'Marechal Cunha Machado', uf: 'MA', regiao: 'Nordeste' },
  { iata: 'IMP', cidade: 'Imperatriz', nome: 'Prefeito Renato Moreira', uf: 'MA', regiao: 'Nordeste' },
  { iata: 'THE', cidade: 'Teresina', nome: 'Senador Petrônio Portella', uf: 'PI', regiao: 'Nordeste' },
  { iata: 'PHB', cidade: 'Parnaíba', nome: 'Prefeito Dr. João Silva Filho', uf: 'PI', regiao: 'Nordeste' },

  // Sul
  { iata: 'POA', cidade: 'Porto Alegre', nome: 'Salgado Filho Internacional', uf: 'RS', regiao: 'Sul' },
  { iata: 'CXJ', cidade: 'Caxias do Sul / Gramado', nome: 'Hugo Cantergiani', uf: 'RS', regiao: 'Sul' },
  { iata: 'PFB', cidade: 'Passo Fundo', nome: 'Lauro Kurtz', uf: 'RS', regiao: 'Sul' },
  { iata: 'FLN', cidade: 'Florianópolis', nome: 'Hercílio Luz Internacional', uf: 'SC', regiao: 'Sul' },
  { iata: 'NVT', cidade: 'Navegantes / Beto Carrero', nome: 'Ministro Victor Konder', uf: 'SC', regiao: 'Sul' },
  { iata: 'XAP', cidade: 'Chapecó', nome: 'Serafin Enoss Bertaso', uf: 'SC', regiao: 'Sul' },
  { iata: 'JOI', cidade: 'Joinville', nome: 'Lauro Carneiro de Loyola', uf: 'SC', regiao: 'Sul' },
  { iata: 'JJG', cidade: 'Jaguaruna', nome: 'Humberto Ghizzo Bortoluzzi', uf: 'SC', regiao: 'Sul' },
  { iata: 'CWB', cidade: 'Curitiba', nome: 'Afonso Pena Internacional', uf: 'PR', regiao: 'Sul' },
  { iata: 'IGU', cidade: 'Foz do Iguaçu', nome: 'Cataratas Internacional', uf: 'PR', regiao: 'Sul' },
  { iata: 'LDB', cidade: 'Londrina', nome: 'Gov. José Richa', uf: 'PR', regiao: 'Sul' },
  { iata: 'MGF', cidade: 'Maringá', nome: 'Sílvio Name Júnior', uf: 'PR', regiao: 'Sul' },
  { iata: 'CAC', cidade: 'Cascavel', nome: 'Adalberto Mendes da Silva', uf: 'PR', regiao: 'Sul' },

  // Centro-Oeste
  { iata: 'BSB', cidade: 'Brasília', nome: 'Presidente Juscelino Kubitschek', uf: 'DF', regiao: 'Centro-Oeste' },
  { iata: 'GYN', cidade: 'Goiânia', nome: 'Santa Genoveva', uf: 'GO', regiao: 'Centro-Oeste' },
  { iata: 'CLV', cidade: 'Caldas Novas', nome: 'Nelson Ribeiro Guimarães', uf: 'GO', regiao: 'Centro-Oeste' },
  { iata: 'CGB', cidade: 'Cuiabá', nome: 'Marechal Rondon', uf: 'MT', regiao: 'Centro-Oeste' },
  { iata: 'OPS', cidade: 'Sinop', nome: 'Presidente João Figueiredo', uf: 'MT', regiao: 'Centro-Oeste' },
  { iata: 'CGR', cidade: 'Campo Grande', nome: 'Campo Grande Internacional', uf: 'MS', regiao: 'Centro-Oeste' },
  { iata: 'BYO', cidade: 'Bonito', nome: 'Regional de Bonito', uf: 'MS', regiao: 'Centro-Oeste' },

  // Norte
  { iata: 'MAO', cidade: 'Manaus', nome: 'Eduardo Gomes Internacional', uf: 'AM', regiao: 'Norte' },
  { iata: 'BEL', cidade: 'Belém', nome: 'Val-de-Cans Internacional', uf: 'PA', regiao: 'Norte' },
  { iata: 'STM', cidade: 'Santarém / Alter do Chão', nome: 'Maestro Wilson Fonseca', uf: 'PA', regiao: 'Norte' },
  { iata: 'MAB', cidade: 'Marabá', nome: 'João Correa da Rocha', uf: 'PA', regiao: 'Norte' },
  { iata: 'PMW', cidade: 'Palmas', nome: 'Brigadeiro Lysias Rodrigues', uf: 'TO', regiao: 'Norte' },
  { iata: 'PVH', cidade: 'Porto Velho', nome: 'Gov. Jorge Teixeira', uf: 'RO', regiao: 'Norte' },
  { iata: 'RBR', cidade: 'Rio Branco', nome: 'Plácido de Castro', uf: 'AC', regiao: 'Norte' },
  { iata: 'MCP', cidade: 'Macapá', nome: 'Alberto Alcolumbre', uf: 'AP', regiao: 'Norte' },
  { iata: 'BVB', cidade: 'Boa Vista', nome: 'Atlas Brasil Cantanhede', uf: 'RR', regiao: 'Norte' },

  // Internacional
  { iata: 'EZE', cidade: 'Buenos Aires', nome: 'Ezeiza Internacional', uf: 'Argentina', regiao: 'Internacional' },
  { iata: 'AEP', cidade: 'Buenos Aires', nome: 'Aeroparque Jorge Newbery', uf: 'Argentina', regiao: 'Internacional' },
  { iata: 'BRC', cidade: 'Bariloche', nome: 'Teniente Luis Candelaria', uf: 'Argentina', regiao: 'Internacional' },
  { iata: 'SCL', cidade: 'Santiago', nome: 'Arturo Merino Benítez', uf: 'Chile', regiao: 'Internacional' },
  { iata: 'MVD', cidade: 'Montevidéu', nome: 'Carrasco Internacional', uf: 'Uruguai', regiao: 'Internacional' },
  { iata: 'LIM', cidade: 'Lima', nome: 'Jorge Chávez Internacional', uf: 'Peru', regiao: 'Internacional' },
  { iata: 'BOG', cidade: 'Bogotá', nome: 'El Dorado Internacional', uf: 'Colômbia', regiao: 'Internacional' },
  { iata: 'CUN', cidade: 'Cancún', nome: 'Cancún Internacional', uf: 'México', regiao: 'Internacional' },
  { iata: 'PUJ', cidade: 'Punta Cana', nome: 'Punta Cana Internacional', uf: 'Rep. Dominicana', regiao: 'Internacional' },
  { iata: 'MIA', cidade: 'Miami', nome: 'Miami International', uf: 'EUA', regiao: 'Internacional' },
  { iata: 'MCO', cidade: 'Orlando', nome: 'Orlando International', uf: 'EUA', regiao: 'Internacional' },
  { iata: 'JFK', cidade: 'Nova York', nome: 'John F. Kennedy International', uf: 'EUA', regiao: 'Internacional' },
  { iata: 'LIS', cidade: 'Lisboa', nome: 'Humberto Delgado', uf: 'Portugal', regiao: 'Internacional' },
  { iata: 'OPO', cidade: 'Porto', nome: 'Francisco Sá Carneiro', uf: 'Portugal', regiao: 'Internacional' },
  { iata: 'MAD', cidade: 'Madri', nome: 'Adolfo Suárez Barajas', uf: 'Espanha', regiao: 'Internacional' },
  { iata: 'BCN', cidade: 'Barcelona', nome: 'El Prat', uf: 'Espanha', regiao: 'Internacional' },
  { iata: 'CDG', cidade: 'Paris', nome: 'Charles de Gaulle', uf: 'França', regiao: 'Internacional' },
  { iata: 'FCO', cidade: 'Roma', nome: 'Fiumicino', uf: 'Itália', regiao: 'Internacional' },
  { iata: 'LHR', cidade: 'Londres', nome: 'Heathrow', uf: 'Reino Unido', regiao: 'Internacional' }
];
