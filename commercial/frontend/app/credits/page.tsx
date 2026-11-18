import { AppHeader } from "@/components/AppHeader";

export default function CreditsPage() {
  return (
    <div className="flex min-h-screen flex-col bg-shell-950 text-ink-100">
      <AppHeader activePage="explorer" />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-8 text-sm leading-6 text-ink-300">
        <h2 className="text-lg font-semibold text-ink-100">Open-source data</h2>
        <p className="mt-3">
          The species list, dex numbers, and type words come from two
          projects. Shiny, Dynamax, Gigantamax, and costume rows are ours,
          restated from announcements a person checked. This build does not
          ship official artwork.
        </p>
        <h3 className="mt-6 font-medium text-ink-100">PvPoke</h3>
        <p className="mt-2">
          GO species, forms, and tags are generated from the PvPoke
          gamemaster. MIT License. Copyright (c) 2019 pvpoke.
        </p>
        <pre className="mt-3 overflow-x-auto rounded-md border border-shell-800 bg-shell-900 p-3 text-xs leading-5 whitespace-pre-wrap">
          {`Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.`}
        </pre>
        <h3 className="mt-6 font-medium text-ink-100">PokéAPI</h3>
        <p className="mt-2">
          National dex numbers and the main-series names and types are from
          PokéAPI. BSD-3-Clause. Copyright (c) 2013-2023 Paul Hallett and
          PokéAPI contributors. Pokémon and Pokémon character names are
          trademarks of Nintendo.
        </p>
        <pre className="mt-3 overflow-x-auto rounded-md border border-shell-800 bg-shell-900 p-3 text-xs leading-5 whitespace-pre-wrap">
          {`Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

Neither the name of PokéAPI nor the names of its contributors may be used
to endorse or promote products derived from this software without specific
prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.`}
        </pre>
      </main>
    </div>
  );
}
