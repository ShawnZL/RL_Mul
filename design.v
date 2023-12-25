module FloatingPointAdder(
  input [7:0] operand_a_mantissa,
  input [7:0] operand_b_mantissa,
  input [2:0] operand_a_exponent,
  input [2:0] operand_b_exponent,
  input operand_a_sign,
  input operand_b_sign,
  output [7:0] result_mantissa,
  output [2:0] result_exponent,
  output result_sign
);

  reg [8:0] extended_operand_a_mantissa;
  reg [8:0] extended_operand_b_mantissa;
  reg [3:0] mantissa_sum;
  reg [3:0] normalized_mantissa_sum;
  reg [2:0] result_exponent_diff;
  reg result_sign;

  always @* begin
    // Extend mantissa by one bit for addition
    extended_operand_a_mantissa = {1'b0, operand_a_mantissa};
    extended_operand_b_mantissa = {1'b0, operand_b_mantissa};

    // Determine the difference in exponents
    result_exponent_diff = operand_a_exponent - operand_b_exponent;

    // Align mantissas based on the exponent difference
    if (result_exponent_diff > 0)
      extended_operand_b_mantissa = {result_exponent_diff, operand_b_mantissa};
    else if (result_exponent_diff < 0)
      extended_operand_a_mantissa = {-result_exponent_diff, operand_a_mantissa};

    // Add or subtract mantissas based on the sign of operand_b
    if (operand_b_sign)
      mantissa_sum = extended_operand_a_mantissa - extended_operand_b_mantissa;
    else
      mantissa_sum = extended_operand_a_mantissa + extended_operand_b_mantissa;

    // Normalize the sum
    normalized_mantissa_sum = mantissa_sum[7:4];

    // Determine the final exponent and sign
    if (mantissa_sum[8]) begin
      result_exponent = operand_a_exponent + result_exponent_diff;
      result_sign = operand_a_sign;
    end
    else begin
      result_exponent = operand_b_exponent;
      result_sign = operand_b_sign;
    end
  end

  assign result_mantissa = normalized_mantissa_sum;

endmodule
