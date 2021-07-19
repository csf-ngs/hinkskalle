<template>
  <div class="about">
    <top-bar title="Some Help!"></top-bar>
    <v-container>
          <v-card>
          <v-tabs vertical>
            <v-tab>
              About
            </v-tab>
            <v-tab>
              Container Types
            </v-tab>
            <v-tab>
              Permissions/Access Control  
            </v-tab>
            <v-tab>
              API
            </v-tab>
            <v-tab-item>
              <v-card flat>
                <v-card-subtitle>
                  <h3>This is Hinkskalle!</h3>
                </v-card-subtitle>
                <v-card-text>
                  <p>Hinkskalle started out as a Singularity container registry compatible with the library 
                    protocol (similar to <a href="https://cloud.sylabs.io/">the Sylabs Cloud</a>), but expanded
                    into a general purpose registry supporting the 
                    <a href="https://github.com/opencontainers/distribution-spec">OCI distribution</a> 
                    protocol (docker, podman, ORAS) and arbitrary data.</p>
                </v-card-text>
              </v-card>
              <v-card>
                <v-card-subtitle>
                  <h3>Library Structure</h3>
                </v-card-subtitle>
                <v-card-text>
                  <p>A Library path looks like this: <code>/entity/collection/container:tag</code></p>
                  <h4>Entity</h4>
                    <p>This is the basic (root) element. You are an entity called <code>{{currentUser.username}}</code>.
                     You can do whatever you like underneath that!</p>
                    <p>We also have a special entity <code>default</code> with some general purpose 
                    containers and data.</p>
                  <h4>Collection</h4>
                    <p>You can group/organize your containers and data into collections. It's up to
                      you how that looks. As an inspiration: This might be by type (docker, singularity, ...)
                      or by project or by purpose.</p>
                  <h4>Container</h4>
                    <p>Now we're getting there, slowly. They contain images and tags pointing to images 
                      (and manifests, minor technical detail). Basically you push your data to a container
                      and link it with a tag.<p>
                  <h4>Image</h4>
                    <p>Some piece of data you push to us. Most likely, a singularity image. Can also be a 
                      docker container layer or some (any) data (if you use oras or the hinkskalle CLI).</p>
                    <p>This data is stored on the server and represented as an image linked to a container</p>
                    <p>You can address/retrieve an image by its sha256 hash</p>
                  <h4>Tag</h4>
                    <p>Since hashes are a bit annoying to handle, you can give your image a name: the tag. This 
                      can be anything (within character limitation reasons), most commonly a version number (like 
                      when you type <code>docker pull ubuntu:20.04</code>).</p>
                  <h4>Examples</h4>
                    <ol>
                      <li>
                        You're working on a project 'smurf-seq' where you need some tools:
                        <ul>
                          <li>/{{currentUser.username}}/smurf-seq/samtools:v1.9</li>
                          <li>/{{currentUser.username}}/smurf-seq/bedtools:v2.28.0</li>
                          <li>/{{currentUser.username}}/smurf-seq/minimap2:v2.17</li>
                        </ul>
                      </li>
                      <li>
                        You decide to organize your genome references and indexes:
                        <ul>
                          <li>/{{currentUser.username}}/genomes/hg19:bowtie2</li>
                          <li>/{{currentUser.username}}/genomes/hg19:fasta</li>
                          <li>/{{currentUser.username}}/genomes/hg19:kallisto</li>
                          <li>/{{currentUser.username}}/genomes/tair10:bowtie2</li>
                          <li>/{{currentUser.username}}/genomes/tair10:fasta</li>
                          <li>/{{currentUser.username}}/genomes/tair10:kallisto</li>
                        </ul>
                      </li>
                      <li>
                        and so on.
                      </li>
                    </ol>
                </v-card-text>
              </v-card>
            </v-tab-item>
            <v-tab-item>
              <v-card flat>
                <v-card-subtitle>
                  <h3>Singularity</h3>
                </v-card-subtitle>
                <v-card-text>
                  <p>Singularity is a nice and light-weight container format/runtime for HPC that you should definitely use.
                    There is a single binary to build (with root permissions) and run (no root needed) your containers.
                    More information: <a href="https://singularity.hpcng.org/">https://singularity.hpcng.org/</a> and 
                    <a href="https://sylabs.io/singularity/">https://sylabs.io/singularity/</a></p>
                  <p>Hinkskalle supports singularity with the <code>library</code> protocol as well as <code>oras</code>.</p>
                  <h4>Library</h4>
                  <p>Configure Hinkskalle as a known remote with a access token:
                    <pre>
  singularity remote add hinkskalle {{backendUrl}}
  # paste token
  singularity remote use hinkskalle
                    </pre>
                  </p>
                  <p>After that you can push/pull your images:
                    <pre>
  singularity push yourimage.sif library://{{currentUser.username}}/[collection]/[container]:[tag]
  singularity pull library://{{currentUser.username}}/[collection]/[container]:[tag]
                    </pre>
                  </p>
                  <h4>ORAS</h4>
                  <pre>
  export SINGULARITY_DOCKER_PASSWORD=[password]
  export SINGULARITY_DOCKER_USERNAME={{currentUser.username}}
  singularity push yourimage.sif oras://{{referenceBase}}/{{currentUser.username}}/[collection]/[container]:[tag]
                  </pre>
                </v-card-text>
              </v-card>
              <v-card flat>
                <v-card-subtitle>
                  <h3>OCI Containers: Docker/Podman/...</h3>
                </v-card-subtitle>
                <v-card-text>
                  <p>Hinkskalle can handle your docker containers as well. Just tag them to the server
                    and push:
                   <pre>
  docker login -u {{currentUser.username}} {{referenceBase}}
  docker push {{referenceBase}}/{{currentUser.username}}/[collection]/[container]:[tag]
  docker pull {{referenceBase}}/{{currentUser.username}}/[collection]/[container]:[tag]
                  </pre>
                  </p>
                </v-card-text>
              </v-card>
              <v-card flat>
                <v-card-subtitle>
                  <h3>ORAS</h3>
                </v-card-subtitle>
                <v-card-text>
                  <p>ORAS stands for OCI Registry As Storage and allows you to push arbitrary files/directories
                    to a OCI registry. You need a command line client, see <a href="https://oras.land/#cli-installation">ORAS</a>.
                   <pre>
  oras login <span v-if="!hasHttps">--insecure</span> -u {{currentUser.username}} {{referenceBase}}
  oras push <span v-if="!hasHttps">--plain-http</span> {{referenceBase}}/{{currentUser.username}}/[collection]/[container]:[tag] \
    file1 file2 ...
  oras pull <span v-if="!hasHttps">--plain-http</span> {{referenceBase}}/{{currentUser.username}}/[collection]/[container]:[tag] 
                  </pre>
                  </p>
                </v-card-text>
              </v-card>
            </v-tab-item>
            <v-tab-item>
              <v-card flat>
                <v-card-subtitle>
                  <h3>Singularity Library</h3>
                </v-card-subtitle>
                <v-card-text>
                  <h4>Pull is Public</h4>
                    <p>It's important to understand: <em>Default Permissions are Public</em>. Anyone 
                      who knows the library URI to your image can pull it, even if they're not logged 
                      in. Call me naive, but it's in the open spirit of science: Share your stuff.</p>
                    <p>You can lock down your containers (maybe they contain your deepest, darkest secrets) by
                      setting the <code>Private</code> flag on them.</p>
                    <p>You can also set a collection to private, then all (new) containers in that collection
                      will be private as well.</p>
                    <p>Or, for complete lockdown, set your entity to <code>defaultPrivate</code>. This means
                      that anything new(!) you push will be private.</p>
                  <h4>Push is Private</h4>
                    <p>You and only you can push to your entity {{currentUser.username}}. That's it!</p>
                </v-card-text>
              </v-card>
              <v-card flat>
                <v-card-subtitle>
                  <h3>All Other Containers</h3>
                </v-card-subtitle>
                <v-card-text>
                  <h4>Pull is Authenticated Only</h4>
                    <p>Docker, ORAS and stuff uploaded with the hinkskalle CLI can be pulled by anyone who is 
                      known to the registry (authenticated users).</p>
                    <p>You can set the container or collection to <code>Private</code> to allow pull only for 
                      yourself.</p>
                    <p>For complete lockdown set your entity to <code>defaultPrivate</code>. This means 
                      that anything new(!) you push will be private.</p>
                  <h4>Push is Private</h4>
                    <p>You and only you can push to your entity {{currentUser.username}}. That's it!</p>
                  <h4>Special Case: Download Tokens</h4>
                    <p>You can generate download URLs with the hinkskalle CLI and the web interface that allow 
                      downloading of exactly this image for everyone having this URL without further authentication 
                      or authorization, even for private images. It contains a special token 
                      that is valid for one day by default (can be configured on the server).</p> 
                </v-card-text>
              </v-card>
              <v-card flat>
                <v-card-subtitle>
                  <h3>Groups/Teams</h3>
                </v-card-subtitle>
                <v-card-text>
                  Sorry, not yet.
                </v-card-text>
              </v-card>
            </v-tab-item>
            <v-tab-item>
              <v-card flat>
                <v-card-subtitle>
                  <h3>JSON API</h3>
                </v-card-subtitle>
                <v-card-text>
                  You can find the auto-generated Swagger/OpenAPI 2.0 specs <a href="/swagger/ui">here</a>
                </v-card-text>
                <v-card-subtitle>
                  <h3>Python Module/CLI</h3>
                </v-card-subtitle>
                <v-card-text>
                  Please check out the companion <a href="https://github.com/csf-ngs/hinkskalle-api">hinkskalle-api</a>
                </v-card-text>
              </v-card>
            </v-tab-item>
          </v-tabs>
          </v-card>
    </v-container>
  </div>
</template>
<style scoped>
.v-card__subtitle, .v-card__text {
  font-size: 1rem;
}

</style>
<script lang="ts">
import { User } from '@/store/models';
import { getEnv } from '@/util/env';
import Vue from 'vue';

export default Vue.extend({
  name: 'About',
  computed: {
    isLoggedIn() {
      return this.$store.getters.isLoggedIn;
    },
    currentUser(): User {
      return this.$store.getters.currentUser;
    },
    backendUrl(): string {
      return getEnv('VUE_APP_BACKEND_URL') as string
    },
    hasHttps(): boolean {
      return this.backendUrl.startsWith('https');
    },
    referenceBase(): string {
      return this.backendUrl.replace(/^https?:\/\//, '').replace(/\/$/, '');
    },
  },
});
</script>