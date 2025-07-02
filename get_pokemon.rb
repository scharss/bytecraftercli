require 'net/http'
require 'uri'
require 'json'

uri = URI.parse('https://pokeapi.co/api/v2/pokemon/ditto')
response = Net::HTTP.get_response(uri)

if response.is_a?(Net::HTTPSuccess)
  pokemon_data = JSON.parse(response.body)
  puts JSON.pretty_generate(pokemon_data)
else
  puts "Error fetching data: #{response.code} #{response.message}"
end